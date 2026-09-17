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
    "lawyer_name": "Dr. Pérez"
  }' | python3 -m json.tool

# 2. Listar casos
curl -s http://localhost:8000/cases | python3 -m json.tool
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

# 5. Agregarle un documento
curl -s -X POST http://localhost:8000/cases/1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Contrato original.pdf",
    "document_type": "contract",
    "file_url": "https://christianbueno.work/cv-es.pdf",
    "uploaded_by": "chris"
  }' | jq