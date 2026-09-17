# Arquitectura y decisiones de diseño

Documento de referencia técnica: patrones aplicados, validaciones, dependencias y el razonamiento detrás de cada decisión relevante del proyecto.

## Organización del código

Arquitectura de capas simple (no Clean Architecture completa — deliberadamente, dado el tamaño del proyecto):

```
config.py    → Settings (variables de entorno)
database.py  → Engine, sesión, Base declarativa
models.py    → Entidades SQLAlchemy (capa de persistencia)
schemas.py   → Contratos de entrada/salida (capa de validación)
routes.py    → Endpoints y lógica de negocio (capa de aplicación)
storage.py   → Abstracción de almacenamiento de archivos
```

## Patrones aplicados

### Dependency Injection (vía FastAPI `Depends`)

`get_db()` en `database.py` es un generador que entrega una `Session` de SQLAlchemy y garantiza su cierre incluso ante excepciones. Se inyecta en cada endpoint con `Depends(get_db)`.

### Strategy / Repository — `storage.py`

`StorageBackend` es una clase abstracta (`ABC`) que define el contrato (`save`, `delete`) para cualquier backend de almacenamiento de archivos. Hoy solo existe `LocalStorageBackend` (disco local, usado en desarrollo), pero el diseño permite agregar `S3StorageBackend`, `AzureBlobStorageBackend` o `DigitalOceanSpacesStorageBackend` sin tocar `routes.py` — solo cambia qué implementación devuelve `get_storage_backend()`.

Motivo: desacoplar la lógica de negocio (subir/borrar un documento de un caso) del proveedor de almacenamiento físico, que casi con certeza va a cambiar entre desarrollo y producción.

### UPSERT atómico para secuencias — generación de `case_number`

`case_number` (ej. `COM-2026-0001`) se genera en el backend combinando `practice_area` + año + un secuencial independiente por esa combinación. Se implementó con una tabla `case_number_sequences` y un `INSERT ... ON CONFLICT DO UPDATE ... RETURNING`, en vez de "buscar el máximo existente y sumar 1".

Motivo: la alternativa ingenua (`SELECT MAX(...) + 1`) tiene una condición de carrera bajo requests concurrentes — dos casos creados casi simultáneamente podrían generar el mismo número. El `UPSERT` es atómico a nivel de fila en PostgreSQL, eliminando esa ventana de colisión.

### Schemas separados por operación (Create / Update / Read)

Cada entidad tiene `EntityCreate` (validación estricta de entrada), `EntityUpdate` (todos los campos opcionales, semántica `PATCH` parcial vía `exclude_unset=True`) y `EntityRead` (lo que se expone al cliente, con `from_attributes=True` para construirse directo desde el ORM). `CaseReadWithDocuments` extiende `CaseRead` agregando la relación anidada, separado del `CaseRead` plano para evitar sobrecargar el listado (`GET /cases`) con datos que no necesita.

## Modelo de datos — decisiones clave

### Tres campos de fecha distintos en `Case`

| Campo | Significado | Tipo |
|---|---|---|
| `opened_at` | Cuándo el cliente contrató a la firma | `datetime`, UTC, timezone-aware |
| `filing_date` | Cuándo se presentó físicamente la demanda ante el juzgado | `date`, sin hora ni timezone |
| `created_at` | Cuándo se registró el caso en el sistema (auditoría técnica) | `datetime`, UTC, timezone-aware |

`filing_date` es intencionalmente un `date` plano (no `datetime`) porque representa un **hecho de calendario ligado a una jurisdicción**, no un instante universal — no tiene sentido "convertir a otra zona horaria" el día en que se presentó una demanda ante un juzgado ecuatoriano.

### Timestamps en UTC (`DateTime(timezone=True)`)

Todas las columnas que representan un instante (`opened_at`, `closed_at`, `created_at`, `updated_at`, `uploaded_at`) usan `DateTime(timezone=True)` en SQLAlchemy y `datetime.now(UTC)` en el código de aplicación — nunca `datetime.now()` naive. Esto evita desfases horarios entre columnas generadas por Python vs. por `server_default=func.now()` de PostgreSQL.

La conversión a hora local (ej. `America/Guayaquil`, UTC-5) es responsabilidad exclusiva del frontend, vía `Intl.DateTimeFormat` con `timeZone` explícito — el backend nunca asume la zona horaria del usuario.

### `PracticeArea` — enum en inglés, mapeo a español en el frontend

Los valores del enum (`COMMERCIAL`, `CIVIL`, `CRIMINAL`, etc.) se mantienen en inglés para consistencia de nomenclatura en el código backend. La traducción a español de Ecuador (`Mercantil`, `Civil`, `Penal`) se resuelve en el frontend Angular con un diccionario de mapeo, no en la API.

### Cascada de borrado

`Case.documents` usa `cascade="all, delete-orphan"` a nivel de ORM y `ForeignKey(..., ondelete="CASCADE")` a nivel de base de datos (doble garantía: cubre tanto borrados vía ORM como cualquier `DELETE` directo por SQL). Eliminar un `Case` elimina automáticamente sus `CaseDocument` asociados.

## Validaciones (`schemas.py`)

- **Strings recortados globalmente** vía `model_config = ConfigDict(str_strip_whitespace=True)` en cada schema — evita espacios en blanco al inicio/fin en cualquier campo de texto sin tener que repetirlo campo por campo.
- **Longitudes mínimas/máximas** alineadas a las columnas de la base de datos (`String(255)`, etc.), para fallar en la capa de validación (HTTP 422) antes de llegar a un error de integridad de PostgreSQL.
- **Fechas no futuras** (`field_validator`): `filing_date` y `opened_at` rechazan valores posteriores al momento actual — un caso no puede abrirse ni una demanda presentarse "en el futuro".
- **`closed_at >= opened_at`**: validación cruzada que vive en `routes.py` (no en el schema), porque requiere comparar contra el valor ya persistido de `opened_at`, que no viaja en el payload de `PATCH`.
- **Cierre automático de casos**: cuando `PATCH /cases/{id}` cambia `status` a `CLOSED` y `closed_at` aún es `null`, el backend asigna `datetime.now(UTC)` automáticamente — sin depender del reloj del cliente. Sigue siendo posible sobreescribir `closed_at` manualmente (por ejemplo, para migrar datos históricos).

## Dependencias principales (`pyproject.toml`)

| Paquete | Propósito |
|---|---|
| `fastapi` | Framework web / definición de endpoints |
| `uvicorn[standard]` | Servidor ASGI |
| `sqlalchemy` | ORM (estilo 2.0, `Mapped`/`mapped_column`) |
| `psycopg[binary]` | Driver de PostgreSQL (usado como `postgresql+psycopg://`) |
| `pydantic-settings` | Carga de configuración desde `.env` con validación de tipos |
| `python-multipart` | Soporte para `multipart/form-data` (subida de archivos) |

## Infraestructura

### PostgreSQL vía Podman

La base de datos corre en un contenedor Podman (imagen `postgres:18.6-trixie`), gestionado por los scripts `scripts/podman/setup-db.sh` y `teardown-db.sh`, que leen su configuración de `.env.db` — completamente separado de `.env` (configuración de la API), para que cada archivo tenga una única responsabilidad.

### `.gitignore` — regla de env vars al final del archivo

La sección de variables de entorno/secretos se ubica deliberadamente al **final** de `.gitignore`. Git aplica la última regla que matchea un archivo dado (no la más específica), así que si esa sección estuviera en medio del archivo, una regla genérica posterior (como `*.db`, pensada para SQLite) podría terminar "decidiendo" el resultado en vez de la regla explícita para `.env`/`.env.db` — funcionalmente correcto por coincidencia, pero fràgil ante cualquier cambio futuro en otras secciones.

## Pendiente / roadmap técnico

- Migraciones con Alembic (hoy se usa `Base.metadata.create_all()` / `drop_all()`, válido solo en fase de prototipo).
- Tests automatizados (pytest).
- Manejo global de excepciones (`IntegrityError` de PostgreSQL → respuesta HTTP controlada).
- Configuración de CORS para el frontend Angular.
- Backend de almacenamiento en la nube (S3/Azure/DigitalOcean) para producción, implementando `StorageBackend`.
