DB_IMAGE=docker.io/library/postgres:18.6-trixie
setup/provisioning, teardown

PROJECT_NAME="crud-store"
NETWORK_NAME="${PROJECT_NAME}-net"
DB_VOL_NAME="${PROJECT_NAME}-db-data"
DB_POD_NAME="${PROJECT_NAME}-db-pod"
DB_BOX_NAME="${PROJECT_NAME}-db-box"

podman volume rm dan-bufete-db-data