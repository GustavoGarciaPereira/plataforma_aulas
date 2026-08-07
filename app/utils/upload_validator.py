"""Validação de arquivos de upload — magic bytes (PDF/JPG/PNG) e tamanho máx.

Independente do storage: decide se o arquivo é aceito e qual extensão usar
(a extensão vem dos bytes, nunca do nome enviado pelo cliente).
"""

from fastapi import UploadFile

MAX_TAMANHO = 10 * 1024 * 1024  # 10MB

# magic bytes por extensão (ordem importa: JPEG começa com \xff\xd8\xff)
_MAGIC_BYTES: dict[str, bytes] = {
    "pdf": b"%PDF",
    "jpg": b"\xff\xd8\xff",
    "png": b"\x89PNG\r\n\x1a\n",
}


def _extensao_por_magic(cabecalho: bytes) -> str | None:
    """Extensão (sem ponto) detectada pelos primeiros bytes do arquivo."""
    for extensao, magic in _MAGIC_BYTES.items():
        if cabecalho.startswith(magic):
            return extensao
    return None


def validar_arquivo(arquivo: UploadFile) -> str:
    """Valida magic bytes e tamanho (<= 10MB); devolve a extensão detectada.

    Lança ValueError se inválido. Deixa o ponteiro do arquivo no início para
    leitura posterior pelo storage.
    """
    arquivo.file.seek(0)
    cabecalho = arquivo.file.read(8)
    extensao = _extensao_por_magic(cabecalho)
    if extensao is None:
        raise ValueError("Formato inválido. Envie PDF, JPG ou PNG.")
    arquivo.file.seek(0, 2)  # fim do arquivo
    tamanho = arquivo.file.tell()
    if tamanho > MAX_TAMANHO:
        raise ValueError("Arquivo muito grande. Tamanho máximo: 10MB.")
    arquivo.file.seek(0)
    return extensao
