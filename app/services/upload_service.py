"""Composição de upload: validação (upload_validator) + storage (StorageBackend).

As funções recebem `storage` como parâmetro (default: `get_storage()`) para
facilitar testes — a camada de negócio (redacao_service) não conhece detalhes
de onde o arquivo é guardado.
"""

from fastapi import UploadFile

from ..storage.base import StorageBackend
from ..storage.factory import get_storage
from ..utils.upload_validator import validar_arquivo


def salvar_upload(storage: StorageBackend | None, arquivo: UploadFile, subpasta: str) -> str:
    """Valida e salva o arquivo; devolve o identificador (caminho relativo)."""
    validar_arquivo(arquivo)
    return (storage or get_storage()).salvar(arquivo, subpasta)


def substituir_upload(
    storage: StorageBackend | None,
    arquivo: UploadFile,
    subpasta: str,
    anterior: str | None,
) -> str:
    """Salva o novo arquivo e remove o anterior (se existir)."""
    novo = salvar_upload(storage, arquivo, subpasta)
    if anterior:
        (storage or get_storage()).deletar(anterior)
    return novo


def deletar_upload(storage: StorageBackend | None, identificador: str | None) -> None:
    """Remove o arquivo identificado (no-op se não existir)."""
    if identificador:
        (storage or get_storage()).deletar(identificador)
