"""Armazenamento local em disco — `uploads/` (configurável via env UPLOADS_DIR)."""

import os
from pathlib import Path

from fastapi import UploadFile

from ..utils.upload_validator import validar_arquivo
from .base import StorageBackend

# Raiz dos uploads (default: pasta uploads/ na raiz do projeto; os testes
# apontam UPLOADS_DIR para um diretório temporário).
RAIZ_UPLOADS = Path(os.environ.get("UPLOADS_DIR", "uploads")).resolve()


class LocalStorage(StorageBackend):
    """Salva arquivos em `{raiz}/{subpasta}/` com nome uuid + extensão detectada."""

    def __init__(self, raiz: Path | None = None) -> None:
        self.raiz = (raiz or RAIZ_UPLOADS).resolve()

    def salvar(self, arquivo: UploadFile, subpasta: str) -> str:
        extensao = validar_arquivo(arquivo)  # garante magic bytes + tamanho
        dados = arquivo.file.read()
        destino_dir = self.raiz / subpasta
        destino_dir.mkdir(parents=True, exist_ok=True)
        nome = self.gerar_nome_unico(f"arquivo.{extensao}")
        (destino_dir / nome).write_bytes(dados)
        return f"{subpasta}/{nome}"

    def deletar(self, identificador: str) -> bool:
        try:
            arquivo = self.obter_path(identificador)
        except ValueError:
            return False
        if arquivo.is_file():
            arquivo.unlink()
            return True
        return False

    def obter_path(self, identificador: str) -> Path:
        """Caminho absoluto garantindo que resolve dentro da raiz (anti traversal)."""
        caminho = (self.raiz / identificador).resolve()
        if not caminho.is_relative_to(self.raiz):
            raise ValueError("Caminho inválido.")
        return caminho
