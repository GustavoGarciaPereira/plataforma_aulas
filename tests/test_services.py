"""Testes unitários da camada de serviços (RF02/RF03).

Usa o fixture `client` do conftest apenas para garantir banco limpo + seed;
os testes chamam os services diretamente com SessionLocal.
"""

import pytest

from app.database import SessionLocal
from app.models import Aula, Turma
from app.services.aula_service import (
    adicionar_aula,
    buscar_aula_da_professora,
    editar_aula,
    excluir_aula,
    mover_aula,
    reordenar_aulas,
)
from app.services.turma_service import (
    criar_turma,
    editar_turma,
    excluir_turma,
    listar_turmas_por_professor,
)

URL_OK = "https://youtu.be/dQw4w9WgXcQ"
URL_RUIM = "https://www.google.com/x"


@pytest.fixture()
def db(client):
    """Sessão isolada por teste (banco já criado/seeded pelo fixture client)."""
    session = SessionLocal()
    yield session
    session.close()


# ---------------------------------------------------------- turma_service --

def test_criar_turma_valida_e_commita(db):
    turma = criar_turma(db, 1, "  Intensivo ENEM  ", "desc", "intensivo")
    assert turma.nome == "Intensivo ENEM" and turma.professor_id == 1
    assert db.get(Turma, turma.id) is not None  # commit persistiu


def test_criar_turma_nome_vazio(db):
    with pytest.raises(ValueError, match="Informe o nome"):
        criar_turma(db, 1, "   ", None, "regular")


def test_criar_turma_tipo_invalido(db):
    with pytest.raises(ValueError, match="Tipo de turma inválido"):
        criar_turma(db, 1, "Turma", None, "premium")


def test_editar_turma_alheia(db):
    outra = criar_turma(db, 999, "Alheia", None, "regular")  # professor 999
    with pytest.raises(ValueError, match="Turma não encontrada"):
        editar_turma(db, outra.id, 1, "Novo nome", None, "regular")


def test_excluir_turma_e_listar(db):
    a = criar_turma(db, 1, "A", None, "regular")
    b = criar_turma(db, 1, "B", None, "regular")
    excluir_turma(db, a.id, 1)
    nomes = [t.nome for t in listar_turmas_por_professor(db, 1)]
    assert nomes == ["B"]  # ordenado por nome


# ---------------------------------------------------------- aula_service ---

def test_adicionar_aula_ordem_automatica(db):
    turma = criar_turma(db, 1, "Turma", None, "regular")
    a1 = adicionar_aula(db, turma.id, 1, "A", URL_OK)
    a2 = adicionar_aula(db, turma.id, 1, "B", URL_OK)
    assert (a1.ordem, a2.ordem) == (1, 2)


def test_adicionar_aula_url_invalida(db):
    turma = criar_turma(db, 1, "Turma", None, "regular")
    with pytest.raises(ValueError, match="URL do YouTube inválida"):
        adicionar_aula(db, turma.id, 1, "A", URL_RUIM)


def test_adicionar_aula_turma_alheia(db):
    with pytest.raises(ValueError, match="Turma não encontrada"):
        adicionar_aula(db, 999, 1, "A", URL_OK)


def test_adicionar_aula_ordem_duplicada(db):
    turma = criar_turma(db, 1, "Turma", None, "regular")
    adicionar_aula(db, turma.id, 1, "A", URL_OK, ordem=1)
    with pytest.raises(ValueError, match="Já existe uma aula nesta posição"):
        adicionar_aula(db, turma.id, 1, "B", URL_OK, ordem=1)


def test_editar_aula_alheia(db):
    turma = criar_turma(db, 999, "Turma alheia", None, "regular")
    aula = adicionar_aula(db, turma.id, 999, "A", URL_OK)
    with pytest.raises(ValueError, match="Aula não encontrada"):
        editar_aula(db, aula.id, 1, "X", URL_OK, 1)


def test_reordenar_aulas(db):
    turma = criar_turma(db, 1, "Turma", None, "regular")
    a1 = adicionar_aula(db, turma.id, 1, "A", URL_OK, ordem=1)
    a3 = adicionar_aula(db, turma.id, 1, "C", URL_OK, ordem=5)
    a2 = adicionar_aula(db, turma.id, 1, "B", URL_OK, ordem=3)
    reordenar_aulas(db, turma.id, 1)
    ordens = {a.titulo: a.ordem for a in [a1, a2, a3]}
    assert ordens == {"A": 1, "B": 2, "C": 3}


def test_mover_aula_swap_e_limite(db):
    turma = criar_turma(db, 1, "Turma", None, "regular")
    a1 = adicionar_aula(db, turma.id, 1, "A", URL_OK, ordem=1)
    a2 = adicionar_aula(db, turma.id, 1, "B", URL_OK, ordem=2)
    assert mover_aula(db, a2.id, 1, "cima") is True
    db.refresh(a1); db.refresh(a2)
    assert (a1.ordem, a2.ordem) == (2, 1)  # trocaram de posição
    # limites (após o swap: a2 é a primeira, a1 é a última)
    assert mover_aula(db, a2.id, 1, "cima") is False
    assert mover_aula(db, a1.id, 1, "baixo") is False


def test_embed_url_property(db):
    turma = criar_turma(db, 1, "Turma", None, "regular")
    boa = adicionar_aula(db, turma.id, 1, "Boa", URL_OK)
    # URL inválida não passa pelo service — insere direto para testar a property
    ruim = Aula(turma_id=turma.id, titulo="Ruim", youtube_url=URL_RUIM, ordem=2)
    db.add(ruim)
    db.commit()
    assert boa.embed_url == "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?rel=0"
    assert ruim.embed_url is None
