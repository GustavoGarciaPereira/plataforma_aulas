"""E2E RF04/RF06 — dashboard, turmas disponíveis e matrícula (TestClient)."""

from app.database import SessionLocal
from app.models import Aula, Matricula, Turma
from tests.conftest import extrair_csrf


def cadastrar_e_logar_aluno(client, email="joao@teste.com"):
    r = client.get("/auth/cadastro")
    token = extrair_csrf(r.text)
    client.post(
        "/auth/cadastro",
        data={
            "nome": "João Teste",
            "email": email,
            "senha": "abc123",
            "confirmar_senha": "abc123",
            "csrf_token": token,
        },
    )
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post(
        "/auth/login",
        data={"email": email, "senha": "abc123", "csrf_token": token},
    )


def logar_professora(client):
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post(
        "/auth/login",
        data={"email": "carla@exemplo.com", "senha": "123456", "csrf_token": token},
    )


def criar_turma_da_carla(client, nome="Intensivo ENEM"):
    logar_professora(client)
    r = client.get("/professor/turmas/nova")
    token = extrair_csrf(r.text)
    client.post(
        "/professor/turmas/nova",
        data={"nome": nome, "descricao": "", "tipo": "intensivo", "csrf_token": token},
    )
    with SessionLocal() as db:
        return db.query(Turma).filter(Turma.nome == nome).one().id


def test_nav_do_aluno_tem_links_reais(client):
    """Regressão: url_for dos templates deve resolver (href real, não '#')."""
    import re as _re

    cadastrar_e_logar_aluno(client, email="nav@teste.com")
    r = client.get("/dashboard")
    # request.url_for gera URL absoluta (ex.: http://testserver/dashboard)
    assert _re.search(r'href="[^"]*/dashboard"', r.text)
    assert _re.search(r'href="[^"]*/turmas-disponiveis"', r.text)
    assert 'href="#"' not in r.text  # nenhum link morto por nome de rota errado


def test_nav_da_professora_tem_link_do_painel(client):
    import re as _re

    logar_professora(client)
    r = client.get("/professor/dashboard")
    assert _re.search(r'href="[^"]*/professor/dashboard"', r.text)
    assert 'href="#"' not in r.text


def test_dashboard_redireciona_anonimo(client):
    r = client.get("/dashboard", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (302, "/auth/login")


def test_dashboard_professora_redireciona_painel(client):
    logar_professora(client)
    r = client.get("/dashboard", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (302, "/professor/dashboard")


def test_dashboard_aluno_vazio(client):
    cadastrar_e_logar_aluno(client)
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "não está matriculado" in r.text


def test_matricula_e_dashboard_com_progresso(client):
    turma_id = criar_turma_da_carla(client)
    # professora sai, aluno entra
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client)

    r = client.get("/turmas-disponiveis")
    assert r.status_code == 200 and "Intensivo ENEM" in r.text
    token = extrair_csrf(r.text)
    r = client.post(
        f"/turmas/{turma_id}/matricular", data={"csrf_token": token}, follow_redirects=False
    )
    assert r.headers["location"] == "/dashboard"

    r = client.get("/dashboard")
    assert "Intensivo ENEM" in r.text
    assert "0%" in r.text and "0 de 0" in r.text  # turma sem aulas
    # card da turma tem link para a página da turma (URL absoluta do url_for)
    assert f"/turmas/{turma_id}" in r.text

    # matrícula idempotente: segundo POST não quebra
    r = client.get("/turmas-disponiveis")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/turmas/{turma_id}/matricular", data={"csrf_token": token}, follow_redirects=False
    )
    assert r.status_code == 303

    # turma inexistente -> flash de erro
    r = client.get("/turmas-disponiveis")
    token = extrair_csrf(r.text)
    r = client.post("/turmas/99999/matricular", data={"csrf_token": token}, follow_redirects=False)
    assert r.headers["location"] == "/turmas-disponiveis"
    assert "Turma não encontrada" in client.get("/turmas-disponiveis").text


def test_progresso_com_aulas_concluidas(client):
    """Dashboard mostra percentual > 0 quando há conclusões (dados diretos)."""
    turma_id = criar_turma_da_carla(client)
    with SessionLocal() as db:
        db.add(
            Aula(
                turma_id=turma_id,
                titulo="Aula 1",
                youtube_url="https://youtu.be/dQw4w9WgXcQ",
                ordem=1,
            )
        )
        db.commit()

    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client, email="maria@teste.com")

    r = client.get("/turmas-disponiveis")
    token = extrair_csrf(r.text)
    client.post(f"/turmas/{turma_id}/matricular", data={"csrf_token": token})

    # simula conclusão via banco (botão de concluir é RF05, próximo prompt)
    with SessionLocal() as db:
        matricula = db.query(Matricula).filter(Matricula.turma_id == turma_id).one()
        db.add(matricula)  # noop
        from app.models import AulaConcluida

        db.add(AulaConcluida(matricula_id=matricula.id, aula_id=db.query(Aula).one().id))
        db.commit()

    r = client.get("/dashboard")
    assert "100%" in r.text
    assert "1 de 1 aulas concluídas" in r.text
    assert "Aula 1" in r.text  # últimas concluídas
