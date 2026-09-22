# API Reference — Dan Bufete API

Referencia completa de endpoints, esquemas de entrada/salida, códigos de estado y ejemplos.

## Base URL

```
http://localhost:8000
```

## Formato

- Todas las peticiones y respuestas usan `application/json`, excepto el endpoint de subida de archivos (`multipart/form-data`).
- Todos los timestamps se devuelven en UTC, formato ISO 8601 con sufijo `Z` (ej. `2026-09-17T05:46:41.731166Z`).
- `filing_date` es una fecha simple sin hora ni zona horaria (ej. `2026-09-15`).

## Formato de errores

Errores de validación (HTTP 422) siguen el formato estándar de FastAPI/Pydantic:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "opened_at"],
      "msg": "Value error, opened_at cannot be in the future",
      "input": "2099-01-01T00:00:00Z",
      "ctx": { "error": {} }
    }
  ]
}
```

Errores de negocio (404, 422 por reglas cruzadas) devuelven:

```json
{
  "detail": "Case not found"
}
```

## Enums

### `PracticeArea`

| Valor | Prefijo en `case_number` |
|---|---|
| `COMMERCIAL` | `COM` |
| `CIVIL` | `CIV` |
| `CRIMINAL` | `CRI` |
| `LABOR` | `LAB` |
| `FAMILY` | `FAM` |
| `ADMINISTRATIVE` | `ADM` |
| `TAX` | `TAX` |
| `CONSTITUTIONAL` | `CON` |

### `CaseStatus`

`open` · `in_progress` · `on_hold` · `closed`

### `CasePriority`

`low` · `medium` · `high`

### `DocumentType`

`contract` · `evidence` · `court_filing` · `correspondence` · `other`

---

## Cases

### `POST /cases`

Crea un nuevo caso. `case_number` se genera automáticamente en el backend (no es un campo de entrada).

**Body**

| Campo | Tipo | Requerido | Reglas |
|---|---|---|---|
| `practice_area` | `PracticeArea` | Sí | — |
| `title` | `string` | Sí | 3–255 caracteres |
| `description` | `string` | Sí | mínimo 10 caracteres |
| `client_name` | `string` | Sí | 2–255 caracteres |
| `lawyer_name` | `string` | Sí | 2–255 caracteres |
| `priority` | `CasePriority` | No | default `medium` |
| `status` | `CaseStatus` | No | default `open` |
| `filing_date` | `date \| null` | No | no puede ser futura |
| `opened_at` | `datetime \| null` | No | no puede ser futura; si se omite, usa la hora actual del servidor |

**Ejemplo de request**

```bash
curl -X POST http://localhost:8000/cases \
  -H "Content-Type: application/json" \
  -d '{
    "practice_area": "COMMERCIAL",
    "title": "Disputa contractual",
    "description": "Incumplimiento de contrato comercial",
    "client_name": "Acme Corp",
    "lawyer_name": "Dr. Pérez"
  }'
```

**Respuesta `201 Created`**

```json
{
  "practice_area": "COMMERCIAL",
  "title": "Disputa contractual",
  "description": "Incumplimiento de contrato comercial",
  "client_name": "Acme Corp",
  "lawyer_name": "Dr. Pérez",
  "priority": "medium",
  "status": "open",
  "id": 1,
  "case_number": "COM-2026-0001",
  "filing_date": null,
  "opened_at": "2026-09-17T05:46:41.731166Z",
  "closed_at": null,
  "created_at": "2026-09-17T05:46:41.728266Z",
  "updated_at": "2026-09-17T05:46:41.728266Z"
}
```

**Errores**

| Código | Causa |
|---|---|
| `422` | Campo faltante, tipo inválido, `title`/`description` fuera de longitud, `filing_date`/`opened_at` futuros |

---

### `GET /cases`

Lista casos, con filtros opcionales y paginación.

**Query params**

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `practice_area` | `PracticeArea` | No | Filtra por área de práctica |
| `status_` | `CaseStatus` | No | Filtra por estado |
| `skip` | `int` | No | Default `0` |
| `limit` | `int` | No | Default `100` |

**Ejemplo**

```bash
curl "http://localhost:8000/cases?practice_area=COMMERCIAL&status_=open&limit=10"
```

**Respuesta `200 OK`**

```json
[
  {
    "practice_area": "COMMERCIAL",
    "title": "Disputa contractual",
    "...": "...",
    "id": 1,
    "case_number": "COM-2026-0001"
  }
]
```

> Nota: este listado **no** incluye `documents` — usa `GET /cases/{id}` para el detalle con documentos anidados.

---

### `GET /cases/{case_id}`

Obtiene un caso por `id`, incluyendo sus documentos.

**Ejemplo**

```bash
curl http://localhost:8000/cases/1
```

**Respuesta `200 OK`**

```json
{
  "practice_area": "COMMERCIAL",
  "title": "Disputa contractual",
  "description": "Incumplimiento de contrato comercial",
  "client_name": "Acme Corp",
  "lawyer_name": "Dr. Pérez",
  "priority": "medium",
  "status": "open",
  "id": 1,
  "case_number": "COM-2026-0001",
  "filing_date": null,
  "opened_at": "2026-09-17T05:46:41.731166Z",
  "closed_at": null,
  "created_at": "2026-09-17T05:46:41.728266Z",
  "updated_at": "2026-09-17T05:46:41.728266Z",
  "documents": [
    {
      "name": "Contrato original.pdf",
      "document_type": "contract",
      "file_url": "/files/450c3b9a-c019-4a46-8cc0-6f79764d1167.pdf",
      "uploaded_by": "chris",
      "id": 1,
      "case_id": 1,
      "uploaded_at": "2026-09-17T22:36:07.577692Z"
    }
  ]
}
```

**Errores**

| Código | Causa |
|---|---|
| `404` | No existe un caso con ese `id` |

---

### `PATCH /cases/{case_id}`

Actualiza parcialmente un caso. Solo se modifican los campos enviados (`exclude_unset`).

**Body** (todos los campos opcionales)

| Campo | Tipo | Reglas |
|---|---|---|
| `title` | `string` | 3–255 caracteres |
| `description` | `string` | mínimo 10 caracteres |
| `client_name` | `string` | 2–255 caracteres |
| `lawyer_name` | `string` | 2–255 caracteres |
| `priority` | `CasePriority` | — |
| `status` | `CaseStatus` | — |
| `filing_date` | `date \| null` | no puede ser futura |
| `closed_at` | `datetime \| null` | no puede ser anterior a `opened_at` |

**Comportamiento especial:** si `status` cambia a `closed` y `closed_at` todavía es `null`, el backend lo asigna automáticamente con la hora actual (UTC) — no es necesario enviarlo.

**Ejemplo — cerrar un caso**

```bash
curl -X PATCH http://localhost:8000/cases/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "closed"}'
```

**Respuesta `200 OK`**

```json
{
  "...": "...",
  "status": "closed",
  "closed_at": "2026-09-17T05:47:01.962626Z",
  "updated_at": "2026-09-17T05:47:01.961568Z"
}
```

**Errores**

| Código | Causa |
|---|---|
| `404` | No existe un caso con ese `id` |
| `422` | `closed_at` anterior a `opened_at`, `filing_date` futura, longitudes inválidas |

---

### `DELETE /cases/{case_id}`

Elimina un caso y, en cascada, todos sus `CaseDocument` asociados.

> **Nota:** este endpoint borra los registros de `CaseDocument` en la base de datos, pero **no** elimina los archivos físicos en disco de esos documentos (a diferencia de `DELETE /cases/{id}/documents/{doc_id}`, que sí lo hace). Ver Roadmap en `ARCHITECTURE.md`.

**Ejemplo**

```bash
curl -X DELETE http://localhost:8000/cases/1
```

**Respuesta:** `204 No Content`

**Errores**

| Código | Causa |
|---|---|
| `404` | No existe un caso con ese `id` |

---

## Case Documents

Recursos anidados bajo `Case` — un `CaseDocument` no existe sin un caso asociado.

Todo documento se crea exclusivamente vía subida física (`POST .../upload`); no existe forma de registrar un documento con una URL externa arbitraria — `storage_key` la genera siempre el `StorageBackend` activo, nunca el cliente.

### `POST /cases/{case_id}/documents/upload`

Sube un archivo físico. El backend lo guarda mediante el `StorageBackend` activo (en desarrollo: disco local, `data/uploads/`, servido en `/files`) y genera `storage_key`/`file_url` automáticamente.

**Content-Type:** `multipart/form-data`

**Campos del form**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `file` | archivo | Sí | El archivo a subir |
| `document_type` | `DocumentType` | Sí | — |
| `uploaded_by` | `string` | Sí | — |
| `name` | `string` | No | Si se omite, usa el nombre original del archivo |

**Ejemplo**

```bash
curl -X POST http://localhost:8000/cases/1/documents/upload \
  -F "file=@/ruta/contrato.pdf" \
  -F "document_type=contract" \
  -F "uploaded_by=chris" \
  -F "name=Contrato de prueba"
```

**Respuesta `201 Created`**

```json
{
  "name": "Contrato de prueba",
  "document_type": "contract",
  "file_url": "/files/450c3b9a-c019-4a46-8cc0-6f79764d1167.pdf",
  "uploaded_by": "chris",
  "id": 1,
  "case_id": 1,
  "uploaded_at": "2026-09-17T22:36:07.577692Z"
}
```

**Errores**

| Código | Causa |
|---|---|
| `404` | El `case_id` no existe |
| `422` | Falta `file`, `document_type` o `uploaded_by` |

---

### `GET /cases/{case_id}/documents`

Lista los documentos de un caso.

**Ejemplo**

```bash
curl http://localhost:8000/cases/1/documents
```

**Respuesta `200 OK`**

```json
[
  {
    "name": "Contrato de prueba",
    "document_type": "contract",
    "file_url": "/files/450c3b9a-c019-4a46-8cc0-6f79764d1167.pdf",
    "uploaded_by": "chris",
    "id": 1,
    "case_id": 1,
    "uploaded_at": "2026-09-17T22:36:07.577692Z"
  }
]
```

**Errores**

| Código | Causa |
|---|---|
| `404` | El `case_id` no existe |

---

### `DELETE /cases/{case_id}/documents/{document_id}`

Elimina un documento: borra tanto el registro en la base de datos como el archivo físico en disco (vía `StorageBackend.delete`).

**Ejemplo**

```bash
curl -X DELETE http://localhost:8000/cases/1/documents/1
```

**Respuesta:** `204 No Content`

**Errores**

| Código | Causa |
|---|---|
| `404` | El documento no existe o no pertenece a ese `case_id` |

---

## Archivos estáticos

### `GET /files/{storage_key}`

Sirve directamente el archivo físico desde `data/uploads/`, montado vía `StaticFiles`. Es la misma URL que devuelve `file_url` en las respuestas de `CaseDocument`. Sin autenticación — acceso directo por diseño para este ejercicio.

**Ejemplo**

```bash
curl -O http://localhost:8000/files/450c3b9a-c019-4a46-8cc0-6f79764d1167.pdf
```

**Errores**

| Código | Causa |
|---|---|
| `404` | No existe un archivo con ese `storage_key` |

---

## Documentación interactiva

Swagger UI y ReDoc se generan automáticamente a partir de este mismo esquema:

- http://localhost:8000/docs
- http://localhost:8000/redoc
  