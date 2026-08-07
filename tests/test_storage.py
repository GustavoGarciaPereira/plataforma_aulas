"""Unitários do storage: LocalStorage (tmp_path), validação e factory."""

import pytest
from fastapi import UploadFile

from app.storage.base import StorageBackend
from app.storage.factory import get_storage
from app.storage.local import LocalStorage
from app.utils.upload_validator import MAX_TAMANHO, validar_arquivo

PDF_VALIDO = b"%PDF-1.4\n1 0 obj\n%%EOF"
EXE_FALSO = b"MZ\x90\x00" + b"\x00" * 64


def _upload_fake(dados: bytes) -> UploadFile:
    """UploadFile com arquivo em memória (implementa seek/read/tell)."""

    class _F:
        def __init__(self, dados):
            self._d = dados
            self._pos = 0

        def seek(self, o, w=0):
            if w == 2:
                self._pos = len(self._d)
                return
            self._pos = o

        def read(self, n=-1):
            fim = len(self._d) if n == -1 else self._pos + n
            r = self._d[self._pos : fim]
            self._pos += len(r)
            return r

        def tell(self):
            return self._pos

    return UploadFile(file=_F(dados))


# ------------------------------------------------------------ validação ---


def test_validar_arquivo_devolve_extensao_detectada():
    assert validar_arquivo(_upload_fake(PDF_VALIDO)) == "pdf"
    assert validar_arquivo(_upload_fake(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)) == "png"
    assert validar_arquivo(_upload_fake(b"\xff\xd8\xff\xe0" + b"\x00" * 8)) == "jpg"
    with pytest.raises(ValueError):
        validar_arquivo(_upload_fake(EXE_FALSO))
    with pytest.raises(ValueError):
        validar_arquivo(_upload_fake(b"%PDF" + b"x" * (MAX_TAMANHO + 1)))


# ------------------------------------------------------- LocalStorage -----


def test_salvar_gera_nome_uuid_e_extensao_detectada(tmp_path):
    storage = LocalStorage(raiz=tmp_path)
    ident = storage.salvar(_upload_fake(PDF_VALIDO), "propostas")
    assert ident.startswith("propostas/") and ident.endswith(".pdf")
    assert (tmp_path / ident).read_bytes() == PDF_VALIDO


def test_salvar_rejeita_formato_invalido(tmp_path):
    storage = LocalStorage(raiz=tmp_path)
    with pytest.raises(ValueError):
        storage.salvar(_upload_fake(EXE_FALSO), "propostas")
    assert not (tmp_path / "propostas").exists()


def test_deletar_remove_e_retorna_bool(tmp_path):
    storage = LocalStorage(raiz=tmp_path)
    ident = storage.salvar(_upload_fake(PDF_VALIDO), "redacoes")
    assert storage.deletar(ident) is True
    assert not (tmp_path / ident).exists()
    assert storage.deletar(ident) is False


def test_obter_path_bloqueia_traversal(tmp_path):
    storage = LocalStorage(raiz=tmp_path)
    with pytest.raises(ValueError):
        storage.obter_path("../../config.py")
    with pytest.raises(ValueError):
        storage.obter_path("propostas/../../../etc/passwd")
    assert storage.obter_path("propostas/a.pdf") == (tmp_path / "propostas" / "a.pdf").resolve()


def test_gerar_nome_unico_sanitiza_extensao(tmp_path):
    storage = LocalStorage(raiz=tmp_path)
    nome = storage.gerar_nome_unico("redação FINAL.PDF")
    assert nome.endswith(".pdf") and len(nome) == 36  # 32 hex + ".pdf"
    sem_ext = storage.gerar_nome_unico("sem_extensao")
    assert len(sem_ext) == 32 and "." not in sem_ext
    assert storage.gerar_nome_unico("a.pdf") != storage.gerar_nome_unico("b.pdf")


# -------------------------------------------------------------- factory ----


def test_factory_respeita_storage_backend(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "storage_backend", "local")
    assert isinstance(get_storage(), StorageBackend)
    assert isinstance(get_storage(), LocalStorage)

    monkeypatch.setattr(config.settings, "storage_backend", "r2")
    with pytest.raises(NotImplementedError):
        get_storage()

    monkeypatch.setattr(config.settings, "storage_backend", "s3")
    with pytest.raises(ValueError):
        get_storage()
