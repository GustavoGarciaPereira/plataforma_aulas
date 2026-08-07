"""Contrato de um backend de armazenamento de uploads.

A validação do arquivo (magic bytes/tamanho) NÃO é responsabilidade do
storage: ela fica em `app/utils/upload_validator.py` e é chamada por quem
compõe a operação (`app/services/upload_service.py`).
"""

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import UploadFile


class StorageBackend(ABC):
    """Interface de armazenamento — `salvar`, `deletar` e `obter_path`."""

    @abstractmethod
    def salvar(self, arquivo: UploadFile, subpasta: str) -> str:
        """Salva o arquivo em `subpasta`; devolve o identificador armazenável.

        Ex.: `"propostas/ab12cd34.pdf"` — é o valor que vai no banco e na URL
        de download (`/uploads/{identificador}`).
        """

    @abstractmethod
    def deletar(self, identificador: str) -> bool:
        """Remove o arquivo; True se existia e foi removido, False caso contrário."""

    @abstractmethod
    def obter_path(self, identificador: str) -> Path:
        """Caminho local do arquivo (para servir via FileResponse).

        Levanta ValueError se o identificador for inválido ou escapar da raiz
        do storage (proteção contra path traversal).
        """

    def gerar_nome_unico(self, nome_original: str) -> str:
        """Nome único (`uuid4().hex`) + extensão sanitizada do nome original.

        A extensão é normalizada (minúsculas, só alfanumérico) e limitada;
        sem extensão válida, devolve apenas o uuid. A camada de negócio deve
        passar aqui a extensão DETECTADA pelos magic bytes, nunca o nome cru
        enviado pelo cliente.
        """
        if "." in nome_original:
            extensao = nome_original.rsplit(".", 1)[-1].lower()
            extensao = "".join(c for c in extensao if c.isalnum())[:10]
        else:
            extensao = ""
        return f"{uuid.uuid4().hex}.{extensao}" if extensao else uuid.uuid4().hex
