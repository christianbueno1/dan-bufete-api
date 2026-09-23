# src/dan_bufete_api/storage.py

import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import UploadFile

from dan_bufete_api.config import get_settings


class StorageBackend(ABC):
    """Contrato que cualquier backend de almacenamiento debe cumplir.

    Implementaciones futuras: S3Storage, AzureBlobStorage, DigitalOceanSpacesStorage.
    """

    @abstractmethod
    def save(self, file: UploadFile) -> str:
        """Guarda el archivo y devuelve su storage_key para persistir en la DB."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, storage_key: str) -> None:
        """Elimina el archivo referenciado por storage_key."""
        raise NotImplementedError

    @abstractmethod
    def get_url(self, storage_key: str) -> str:
        """Devuelve la URL pública (absoluta) para acceder al archivo."""
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    """Backend de desarrollo/producción simple: guarda archivos en disco local."""

    def __init__(
        self,
        base_dir: str = "data/uploads",
        url_prefix: str = "/files",
        base_url: str = "http://localhost:8000",
    ):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.url_prefix = url_prefix.rstrip("/")
        self.base_url = base_url.rstrip("/")

    def save(self, file: UploadFile) -> str:
        extension = Path(file.filename or "").suffix
        storage_key = f"{uuid.uuid4()}{extension}"
        destination = self.base_dir / storage_key

        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return storage_key

    def delete(self, storage_key: str) -> None:
        path = self._safe_path(storage_key)
        if path.exists():
            path.unlink()

    def get_url(self, storage_key: str) -> str:
        return f"{self.base_url}{self.url_prefix}/{storage_key}"

    def _safe_path(self, storage_key: str) -> Path:
        candidate = (self.base_dir / storage_key).resolve()
        if self.base_dir.resolve() not in candidate.parents:
            raise ValueError("storage_key inválida")
        return candidate


def get_storage_backend() -> StorageBackend:
    """Factory: hoy siempre local; en el futuro lee de settings (STORAGE_BACKEND=s3, etc.)."""
    settings = get_settings()
    return LocalStorageBackend(base_url=settings.api_base_url)