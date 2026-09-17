# src/dan_bufete_api/storage.py

import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import UploadFile


class StorageBackend(ABC):
    """Contrato que cualquier backend de almacenamiento debe cumplir.

    Implementaciones futuras: S3Storage, AzureBlobStorage, DigitalOceanSpacesStorage.
    """

    @abstractmethod
    def save(self, file: UploadFile) -> str:
        """Guarda el archivo y devuelve su file_url (o path) para persistir en la DB."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, file_url: str) -> None:
        """Elimina el archivo referenciado por file_url."""
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    """Backend de desarrollo: guarda archivos en disco local."""

    def __init__(self, base_dir: str = "data/uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file: UploadFile) -> str:
        extension = Path(file.filename or "").suffix
        unique_name = f"{uuid.uuid4()}{extension}"
        destination = self.base_dir / unique_name

        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return str(destination)

    def delete(self, file_url: str) -> None:
        path = Path(file_url)
        if path.exists():
            path.unlink()


def get_storage_backend() -> StorageBackend:
    """Factory: hoy siempre local; en el futuro lee de settings (STORAGE_BACKEND=s3, etc.)."""
    return LocalStorageBackend()
