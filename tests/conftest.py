"""Fixtures compartilhadas — banco SQLite temporário + TestClient.

Importante: o DATABASE_URL é definido ANTES de importar qualquer módulo app.*
(engine/seed leem a variável no import).
"""

import os
import re
import tempfile
from pathlib import Path

_tmp_db = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"

import pytest
from starlette.testclient import TestClient

from app.database import Base, engine
from app.seed import main as seed_main


@pytest.fixture()
def client():
    """TestClient com banco limpo a cada teste (SQLite em /tmp)."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    seed_main()  # professora Carla (carla@exemplo.com / 123456)
    from app.main import app

    with TestClient(app) as c:
        yield c


def extrair_csrf(texto: str) -> str:
    """Extrai o token CSRF de um HTML renderizado."""
    m = re.search(r'name="csrf_token" value="([^"]+)"', texto)
    assert m, "token CSRF não encontrado no HTML"
    return m.group(1)


@pytest.fixture()
def login_professora(client):
    """Loga como Carla (seed) e devolve helper para POSTs com CSRF."""

    def _login() -> dict:
        r = client.get("/auth/login")
        token = extrair_csrf(r.text)
        r = client.post(
            "/auth/login",
            data={"email": "carla@exemplo.com", "senha": "123456", "csrf_token": token},
            follow_redirects=False,
        )
        assert (r.status_code, r.headers["location"]) == (303, "/professor/dashboard")
        return {"csrf": token}

    return _login
