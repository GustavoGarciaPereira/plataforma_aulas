"""Upload de arquivos — proposta de redação e submissão (PDF/JPG/PNG, máx 10MB).

Validação por **magic bytes** (não por extensão) e armazenamento local em
`uploads/{subpasta}/`. O nome do arquivo é `uuid4().hex` + extensão detectada
pelos bytes — o nome original do cliente nunca é usado (evita injeção/enganos).

A pasta raiz é configurável via env `UPLOADS_DIR` (default `uploads/` na raiz
do projeto); os testes apontam para um diretório temporário.
"""

import os
import uuid
from pathlib import Path

from fastapi import UploadFile

MAX_TAMANHO = 10 * 1024 * 1024  # 10MB

# magic bytes por extensão detectada (ordem importa: JPEG começa com \xff\xd8\xff)
_MAGIC_BYTES: dict[str, bytes] = {
    "pdf": b"%PDF",
    "jpg": b"\xff\xd8\xff",
    "png": b"\x89PNG\r\n\x1a\n",
}

RAIZ_UPLOADS = Path(os.environ.get("UPLOADS_DIR", "uploads")).resolve()


def _extensao_por_magic(cabecalho: bytes) -> str | None:
    """Extensão (sem ponto) detectada pelos primeiros bytes do arquivo."""
    for extensao, magic in _MAGIC_BYTES.items():
        if cabecalho.startswith(magic):
            return extensao
    return None


def validar_arquivo(arquivo: UploadFile) -> None:
    """Valida magic bytes e tamanho (<= 10MB). Lança ValueError se inválido.

    Deixa o ponteiro do arquivo no início para leitura posterior.
    """
    arquivo.file.seek(0)
    cabecalho = arquivo.file.read(8)
    if _extensao_por_magic(cabecalho) is None:
        raise ValueError("Formato inválido. Envie PDF, JPG ou PNG.")
    arquivo.file.seek(0, 2)  # fim do arquivo
    tamanho = arquivo.file.tell()
    if tamanho > MAX_TAMANHO:
        raise ValueError("Arquivo muito grande. Tamanho máximo: 10MB.")
    arquivo.file.seek(0)


def salvar_upload(arquivo: UploadFile, subpasta: str) -> str:
    """Valida e salva em `uploads/{subpasta}/`; devolve caminho relativo.

    Ex.: `salvar_upload(arquivo, "propostas")` -> `"propostas/ab12cd34.pdf"`
    (é esse valor que vai no banco e na URL `/uploads/{caminho}`).
    """
    validar_arquivo(arquivo)
    dados = arquivo.file.read()
    extensao = _extensao_por_magic(dados[:8])
    assert extensao is not None  # validar_arquivo já garantiu
    destino_dir = RAIZ_UPLOADS / subpasta
    destino_dir.mkdir(parents=True, exist_ok=True)
    nome = f"{uuid.uuid4().hex}.{extensao}"
    (destino_dir / nome).write_bytes(dados)
    return f"{subpasta}/{nome}"


def caminho_absoluto(caminho_relativo: str) -> Path:
    """Caminho absoluto garantindo que resolve dentro de uploads/ (anti path traversal)."""
    raiz = RAIZ_UPLOADS.resolve()
    caminho = (raiz / caminho_relativo).resolve()
    if not caminho.is_relative_to(raiz):
        raise ValueError("Caminho inválido.")
    return caminho


def deletar_arquivo(caminho_relativo: str | None) -> None:
    """Remove o arquivo de uploads/ se existir (caminho relativo armazenado no banco)."""
    if not caminho_relativo:
        return
    try:
        arquivo = caminho_absoluto(caminho_relativo)
    except ValueError:
        return
    arquivo.unlink(missing_ok=True)
