# Dan Bufete API

API REST CRUD para gestión de casos legales de un bufete de abogados, construida con FastAPI y PostgreSQL.

## Stack técnico

- **Lenguaje / Framework:** Python 3.14, FastAPI
- **ORM:** SQLAlchemy 2.0 (estilo `Mapped` / `mapped_column`)
- **Validación:** Pydantic v2 (`pydantic-settings` para configuración)
- **Base de datos:** PostgreSQL 18.6, contenerizada con Podman
- **Gestor de paquetes:** uv
- **Servidor ASGI:** Uvicorn

## Entorno de desarrollo

- **SO:** Fedora Linux 44
- **Contenedores:** Podman (pods, sin Docker)
- **Editor:** VS Code
- **Control de versiones:** Git
- **Shell:** Bash
- **Asistentes de desarrollo:** Claude Code, Codex CLI, Gemini CLI

## Requisitos previos

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Podman

## Configuración inicial

### 1. Instalar dependencias

```bash
uv sync
```

### 2. Configurar variables de entorno

El proyecto usa dos archivos de entorno separados por responsabilidad:

| Archivo | Propósito | Quién lo lee |
|---|---|---|
| `.env` | Configuración de la API (conexión a la DB, debug) | La aplicación FastAPI |
| `.env.db` | Configuración de Podman/PostgreSQL (imagen, nombres de pod/red/volumen, credenciales de inicialización) | Scripts de `scripts/podman/` |

```bash
cp .env.example .env
cp .env.db.example .env.db
```

Edita ambos archivos con tus valores reales antes de continuar.

### 3. Levantar PostgreSQL con Podman

```bash
./scripts/podman/setup-db.sh
```

Para detener y eliminar el contenedor:

```bash
./scripts/podman/teardown-db.sh
```

## Ejecutar la API

```bash
uv run uvicorn dan_bufete_api.main:app --reload
```

El esquema de base de datos (`cases`, `case_documents`, `case_number_sequences`) se crea automáticamente al arrancar la aplicación (`Base.metadata.create_all()` en el `lifespan` de `main.py`) — no requiere ningún paso manual adicional tras levantar PostgreSQL.

- API: http://localhost:8000
- Documentación interactiva (Swagger UI): http://localhost:8000/docs
- Documentación alternativa (ReDoc): http://localhost:8000/redoc

## Almacenamiento de archivos

Los documentos subidos se guardan en `data/uploads/` (backend local, ver `storage.py`) y se sirven directamente vía `StaticFiles` montado en `/files` (sin autenticación — suficiente para este ejercicio). La abstracción `StorageBackend` permite reemplazar este backend por uno en la nube (S3, Azure, DigitalOcean Spaces) sin tocar `routes.py`.

## Estructura del proyecto

```
src/dan_bufete_api/
├── main.py        # Punto de entrada de FastAPI, lifespan (create_all), mount de /files, registro de routers
├── config.py       # Settings (pydantic-settings), lee .env
├── database.py     # Engine, SessionLocal, Base declarativa, get_db()
├── models.py       # Modelos SQLAlchemy (Case, CaseDocument, enums)
├── schemas.py       # Schemas Pydantic (Create/Update/Read)
├── routes.py       # Endpoints CRUD, lógica de negocio
└── storage.py       # Abstracción de almacenamiento de archivos (StorageBackend, LocalStorageBackend)

scripts/podman/
├── setup-db.sh      # Levanta el contenedor de PostgreSQL
└── teardown-db.sh   # Detiene y elimina el contenedor
```

Para más detalle sobre patrones, decisiones de diseño y validaciones, ver [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/cases` | Crear un caso |
| `GET` | `/cases` | Listar casos (filtros por `practice_area`, `status`) |
| `GET` | `/cases/{id}` | Obtener un caso con sus documentos |
| `PATCH` | `/cases/{id}` | Actualizar un caso |
| `DELETE` | `/cases/{id}` | Eliminar un caso (y sus documentos en cascada) |
| `POST` | `/cases/{id}/documents/upload` | Subir un archivo físico (multipart/form-data) |
| `GET` | `/cases/{id}/documents` | Listar documentos de un caso |
| `DELETE` | `/cases/{id}/documents/{doc_id}` | Eliminar un documento (registro + archivo) |
| `GET` | `/files/{storage_key}` | Servir el archivo físico (estático, sin auth) |

## Feed de la base de datos
```bash
uv run python scripts/seed_db.py
```

## Licencia

Privado — uso interno.
