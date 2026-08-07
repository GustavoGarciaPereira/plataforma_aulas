"""Factory do storage backend — alterna por STORAGE_BACKEND (default: 'local')."""

from ..config import settings
from .base import StorageBackend
from .local import LocalStorage


def get_storage() -> StorageBackend:
    """Devolve o backend configurado em `STORAGE_BACKEND` ('local' | 'r2')."""
    if settings.storage_backend == "local":
        return LocalStorage()
    if settings.storage_backend == "r2":
        raise NotImplementedError(
            "STORAGE_BACKEND=r2 ainda não está implementado. "
            "Use 'local' ou implemente R2Storage (ver app/storage/r2.py)."
        )
    raise ValueError(
        f"STORAGE_BACKEND inválido: {settings.storage_backend!r} (esperado 'local' ou 'r2')."
    )
