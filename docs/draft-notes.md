## commands 
```bash
DB_IMAGE=docker.io/library/postgres:18.6-trixie
setup/provisioning, teardown

PROJECT_NAME="crud-store"
NETWORK_NAME="${PROJECT_NAME}-net"
DB_VOL_NAME="${PROJECT_NAME}-db-data"
DB_POD_NAME="${PROJECT_NAME}-db-pod"
DB_BOX_NAME="${PROJECT_NAME}-db-box"

podman volume rm dan-bufete-db-data

podman exec -it dan-bufete-db-box psql -U krs -d dan_bufete_db -c "\dt"
podman exec -it dan-bufete-db-box psql -U krs -d dan_bufete_db -x -c "select * from cases;"

```
# Esto es especialmente útil ahora porque queremos inspeccionar los datos que realmente devuelve la API, no solamente leer API_REFERENCE.md.
curl -s http://localhost:8000/cases | python3 -m json.tool

## test endpoints
```bash
# 1. Crear un caso
curl -s -X POST http://localhost:8000/cases \
  -H "Content-Type: application/json" \
  -d '{
    "practice_area": "COMMERCIAL",
    "title": "Disputa contractual",
    "description": "Incumplimiento de contrato comercial",
    "client_name": "Acme Corp",
    "lawyer_name": "Dr. Pérez",
    "opened_at": "2026-08-30T10:00:00Z"
  }' | jq

# 2. Listar casos
curl -s http://localhost:8000/cases | jq

# 3. Crear otro caso de la misma área para confirmar la secuencia
curl -s -X POST http://localhost:8000/cases \
  -H "Content-Type: application/json" \
  -d '{
    "practice_area": "COMMERCIAL",
    "title": "Segundo caso comercial",
    "description": "Prueba de secuencia",
    "client_name": "Beta SA",
    "lawyer_name": "Dra. Gómez"
  }' | jq

# 4. Obtener el detalle del primer caso (usa el "id" que te devolvió el paso 1, no el case_number)
curl -s http://localhost:8000/cases/1 | jq

# delete case
curl -s -X DELETE http://localhost:8000/cases/5 -w "\n%{http_code}\n"
curl -s http://localhost:8000/cases | jq

# 5. Agregarle un documento
curl -s -X POST http://localhost:8000/cases/1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Contrato original.pdf",
    "document_type": "contract",
    "file_url": "https://christianbueno.work/cv-es.pdf",
    "uploaded_by": "chris"
  }' | jq

# 6. Confirmar que el caso ahora trae el documento anidado
curl -s http://localhost:8000/cases/1 | jq

# document upload
echo "contenido de prueba" > /tmp/contrato-test.pdf

curl -s -X POST http://localhost:8000/cases/1/documents/upload \
  -F "file=@/tmp/contrato-test.pdf" \
  -F "document_type=contract" \
  -F "uploaded_by=chris" \
  -F "name=Contrato de prueba" | jq

curl -s http://localhost:8000/cases/1 | jq '.documents'

# Probar el delete y confirmar que el archivo desaparece del disco también
curl -s -X DELETE http://localhost:8000/cases/1/documents/1 -w "\n%{http_code}\n"
ls -la data/uploads/

# Debe fallar con 422 — fecha futura
curl -s -X POST http://localhost:8000/cases \
  -H "Content-Type: application/json" \
  -d '{
    "practice_area": "CIVIL",
    "title": "Caso futuro",
    "description": "Prueba de validación",
    "client_name": "Test",
    "lawyer_name": "Test",
    "opened_at": "2099-01-01T00:00:00Z"
  }' -w "\n%{http_code}\n"
```

## Recrear el esquema y verificar
```bash
uv run python -c "
from dan_bufete_api.database import Base, engine
from dan_bufete_api import models
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print('Tablas recreadas:', list(Base.metadata.tables.keys()))
"
```

API_URL=http://localhost:8000

## Scripts
```bash
chmod +x scripts/api-smoke-test.sh
```