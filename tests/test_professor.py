"""E2E RF02/RF03 — gestão de turmas e aulas pela professora (TestClient)."""

from app.database import SessionLocal
from app.models import Aula, Professor, Turma
from app.security import hash_senha
from tests.conftest import extrair_csrf

URL_YT_VALIDA = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
URL_YT_INVALIDA = "https://www.google.com/nao-e-youtube"


def criar_turma(client, csrf, nome="Intensivo ENEM", **extra) -> int:
    """Cria uma turma via POST e devolve o id (lido do banco)."""
    r = client.get("/professor/turmas/nova")
    token = extrair_csrf(r.text)
    r = client.post(
        "/professor/turmas/nova",
        data={
            "nome": nome,
            "descricao": extra.get("descricao", ""),
            "tipo": extra.get("tipo", "intensivo"),
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert (r.status_code, r.headers["location"]) == (303, "/professor/dashboard")
    with SessionLocal() as db:
        return db.query(Turma).filter(Turma.nome == nome).one().id


def criar_aula(client, turma_id, titulo="Aula 1", url=URL_YT_VALIDA, ordem="") -> int:
    r = client.get(f"/professor/turmas/{turma_id}/aulas/nova")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/professor/turmas/{turma_id}/aulas/nova",
        data={"titulo": titulo, "youtube_url": url, "ordem": ordem, "csrf_token": token},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text[:300]
    with SessionLocal() as db:
        return db.query(Aula).filter(Aula.titulo == titulo).one().id


# ---------------------------------------------------------------- acesso ---


def test_dashboard_redireciona_anonimo(client):
    r = client.get("/professor/dashboard", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (302, "/auth/login")


def test_dashboard_bloqueia_aluno(client):
    # cadastro de aluno + login
    r = client.get("/auth/cadastro")
    token = extrair_csrf(r.text)
    client.post(
        "/auth/cadastro",
        data={
            "nome": "João",
            "email": "joao@aluno.com",
            "senha": "abc123",
            "confirmar_senha": "abc123",
            "csrf_token": token,
        },
    )
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post(
        "/auth/login", data={"email": "joao@aluno.com", "senha": "abc123", "csrf_token": token}
    )
    r = client.get("/professor/dashboard", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (302, "/dashboard")


# ----------------------------------------------------------------- RF02 ---


def test_form_turma_tem_select_tipo(client, login_professora):
    """Regressão: o select 'Tipo' precisa renderizar as 3 opções (RF02)."""
    login_professora()
    r = client.get("/professor/turmas/nova")
    assert r.status_code == 200
    for opcao in ("intensivo", "regular", "outro"):
        assert f'<option value="{opcao}"' in r.text, f"opção {opcao} ausente"

    # edição: opção atual vem pré-selecionada
    turma_id = criar_turma(client, None, nome="Select Teste", tipo="intensivo")
    r = client.get(f"/professor/turmas/{turma_id}/editar")
    assert '<option value="intensivo" selected' in r.text


def test_criar_turma(client, login_professora):
    login_professora()
    turma_id = criar_turma(client, None)
    r = client.get("/professor/dashboard")
    assert "Intensivo ENEM" in r.text
    assert "Turma criada com sucesso!" in r.text or "Intensivo ENEM" in r.text
    with SessionLocal() as db:
        turma = db.get(Turma, turma_id)
        assert turma.tipo == "intensivo" and turma.descricao == ""


def test_criar_turma_sem_csrf_rejeitado(client, login_professora):
    login_professora()
    r = client.post(
        "/professor/turmas/nova",
        data={"nome": "X", "descricao": "", "tipo": "regular"},
        follow_redirects=False,
    )
    assert r.status_code == 303  # rejeitado -> redirecionado de volta
    with SessionLocal() as db:
        assert db.query(Turma).filter(Turma.nome == "X").first() is None


def test_editar_turma(client, login_professora):
    login_professora()
    turma_id = criar_turma(client, None)
    r = client.get(f"/professor/turmas/{turma_id}/editar")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/professor/turmas/{turma_id}/editar",
        data={
            "nome": "Regular FUVEST",
            "descricao": "Nova desc",
            "tipo": "regular",
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert (r.status_code, r.headers["location"]) == (303, "/professor/dashboard")
    with SessionLocal() as db:
        turma = db.get(Turma, turma_id)
        assert turma.nome == "Regular FUVEST" and turma.tipo == "regular"


def test_excluir_turma_cascata(client, login_professora):
    login_professora()
    turma_id = criar_turma(client, None)
    aula_id = criar_aula(client, turma_id)
    r = client.get("/professor/dashboard")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/professor/turmas/{turma_id}/excluir", data={"csrf_token": token}, follow_redirects=False
    )
    assert (r.status_code, r.headers["location"]) == (303, "/professor/dashboard")
    with SessionLocal() as db:
        assert db.get(Turma, turma_id) is None
        assert db.get(Aula, aula_id) is None  # cascade funcionou


def test_turma_de_outro_professor_inacessivel(client, login_professora):
    login_professora()
    with SessionLocal() as db:
        outra = Professor(nome="Outra", email="outra@ex.com", senha_hash=hash_senha("x"))
        db.add(outra)
        db.flush()
        t = Turma(nome="Turma Alheia", descricao="", tipo="regular", professor_id=outra.id)
        db.add(t)
        db.commit()
        turma_id = t.id
    r = client.get(f"/professor/turmas/{turma_id}/editar", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (303, "/professor/dashboard")
    assert "Turma não encontrada" in client.get("/professor/dashboard").text


# ----------------------------------------------------------------- RF03 ---


def test_criar_aula_url_valida(client, login_professora):
    login_professora()
    turma_id = criar_turma(client, None)
    r = client.get(f"/professor/turmas/{turma_id}/aulas/nova")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/professor/turmas/{turma_id}/aulas/nova",
        data={
            "titulo": "Introdução à redação",
            "youtube_url": URL_YT_VALIDA,
            "ordem": "",
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert (r.status_code, r.headers["location"]) == (303, f"/professor/turmas/{turma_id}/aulas")
    r = client.get(f"/professor/turmas/{turma_id}/aulas")
    assert "Introdução à redação" in r.text
    assert "youtube.com/embed/dQw4w9WgXcQ" in r.text  # embed gerado
    with SessionLocal() as db:
        aula = db.query(Aula).filter(Aula.turma_id == turma_id).one()
        assert aula.ordem == 1  # ordem automática


def test_criar_aula_url_invalida(client, login_professora):
    login_professora()
    turma_id = criar_turma(client, None)
    r = client.get(f"/professor/turmas/{turma_id}/aulas/nova")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/professor/turmas/{turma_id}/aulas/nova",
        data={"titulo": "X", "youtube_url": URL_YT_INVALIDA, "ordem": "", "csrf_token": token},
        follow_redirects=False,
    )
    assert r.headers["location"] == f"/professor/turmas/{turma_id}/aulas/nova"
    assert "URL do YouTube inválida" in client.get(f"/professor/turmas/{turma_id}/aulas/nova").text
    with SessionLocal() as db:
        assert db.query(Aula).filter(Aula.turma_id == turma_id).count() == 0


def test_ordem_automatica_sequencial(client, login_professora):
    login_professora()
    turma_id = criar_turma(client, None)
    criar_aula(client, turma_id, "A", ordem="")
    criar_aula(client, turma_id, "B", ordem="")
    criar_aula(client, turma_id, "C", ordem="")
    with SessionLocal() as db:
        ordens = [
            a.ordem
            for a in db.query(Aula).filter(Aula.turma_id == turma_id).order_by(Aula.ordem).all()
        ]
        assert ordens == [1, 2, 3]


def test_ordem_duplicada_rejeitada(client, login_professora):
    login_professora()
    turma_id = criar_turma(client, None)
    criar_aula(client, turma_id, "Primeira", ordem="1")
    r = client.get(f"/professor/turmas/{turma_id}/aulas/nova")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/professor/turmas/{turma_id}/aulas/nova",
        data={"titulo": "Segunda", "youtube_url": URL_YT_VALIDA, "ordem": "1", "csrf_token": token},
        follow_redirects=False,
    )
    assert r.headers["location"] == f"/professor/turmas/{turma_id}/aulas/nova"
    assert (
        "Já existe uma aula nesta posição"
        in client.get(f"/professor/turmas/{turma_id}/aulas/nova").text
    )


def test_editar_aula(client, login_professora):
    login_professora()
    turma_id = criar_turma(client, None)
    aula_id = criar_aula(client, turma_id, "Título Antigo")
    r = client.get(f"/professor/aulas/{aula_id}/editar")
    assert "Título Antigo" in r.text  # formulário pré-preenchido
    token = extrair_csrf(r.text)
    r = client.post(
        f"/professor/aulas/{aula_id}/editar",
        data={
            "titulo": "Título Novo",
            "youtube_url": URL_YT_VALIDA,
            "ordem": "5",
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert r.headers["location"] == f"/professor/turmas/{turma_id}/aulas"
    with SessionLocal() as db:
        aula = db.get(Aula, aula_id)
        assert aula.titulo == "Título Novo" and aula.ordem == 5


def test_mover_aula(client, login_professora):
    login_professora()
    turma_id = criar_turma(client, None)
    id_a = criar_aula(client, turma_id, "A", ordem="1")
    id_b = criar_aula(client, turma_id, "B", ordem="2")
    id_c = criar_aula(client, turma_id, "C", ordem="3")

    # B sobe -> ordens [2, 1, 3]
    r = client.get(f"/professor/turmas/{turma_id}/aulas")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/professor/aulas/{id_b}/mover",
        data={"direcao": "cima", "csrf_token": token},
        follow_redirects=False,
    )
    assert r.status_code == 303
    with SessionLocal() as db:
        ordens = {a.id: a.ordem for a in db.query(Aula).filter(Aula.turma_id == turma_id).all()}
        assert (ordens[id_a], ordens[id_b], ordens[id_c]) == (2, 1, 3)

    # B desce -> volta [1, 2, 3]
    token = extrair_csrf(client.get(f"/professor/turmas/{turma_id}/aulas").text)
    client.post(f"/professor/aulas/{id_b}/mover", data={"direcao": "baixo", "csrf_token": token})
    with SessionLocal() as db:
        ordens = {a.id: a.ordem for a in db.query(Aula).filter(Aula.turma_id == turma_id).all()}
        assert (ordens[id_a], ordens[id_b], ordens[id_c]) == (1, 2, 3)

    # A tenta subir (já é a primeira) -> sem erro
    token = extrair_csrf(client.get(f"/professor/turmas/{turma_id}/aulas").text)
    r = client.post(
        f"/professor/aulas/{id_a}/mover",
        data={"direcao": "cima", "csrf_token": token},
        follow_redirects=False,
    )
    assert r.status_code == 303


def test_excluir_aula(client, login_professora):
    login_professora()
    turma_id = criar_turma(client, None)
    aula_id = criar_aula(client, turma_id, "Para Excluir")
    r = client.get(f"/professor/turmas/{turma_id}/aulas")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/professor/aulas/{aula_id}/excluir", data={"csrf_token": token}, follow_redirects=False
    )
    assert r.headers["location"] == f"/professor/turmas/{turma_id}/aulas"
    with SessionLocal() as db:
        assert db.get(Aula, aula_id) is None


def test_aula_de_turma_alheia_inacessivel(client, login_professora):
    login_professora()
    with SessionLocal() as db:
        outra = Professor(nome="Outra2", email="outra2@ex.com", senha_hash=hash_senha("x"))
        db.add(outra)
        db.flush()
        t = Turma(nome="Turma Alheia 2", descricao="", tipo="regular", professor_id=outra.id)
        db.add(t)
        db.commit()
        a = Aula(turma_id=t.id, titulo="Aula Alheia", youtube_url=URL_YT_VALIDA, ordem=1)
        db.add(a)
        db.commit()
        aula_id = a.id
    r = client.get(f"/professor/aulas/{aula_id}/editar", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (303, "/professor/dashboard")
