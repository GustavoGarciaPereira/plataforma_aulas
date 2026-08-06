"""E2E RF05/RF07 — página da turma, conclusão de aula e cronograma."""

from app.database import SessionLocal
from app.models import Aula, Turma
from tests.conftest import extrair_csrf
from tests.test_aluno import cadastrar_e_logar_aluno, criar_turma_da_carla, logar_professora

URL_OK = "https://youtu.be/dQw4w9WgXcQ"


def criar_turma_com_aulas(client, nome="Intensivo ENEM", n_aulas=2) -> int:
    turma_id = criar_turma_da_carla(client, nome)
    with SessionLocal() as db:
        for i in range(1, n_aulas + 1):
            db.add(Aula(turma_id=turma_id, titulo=f"Aula {i}", youtube_url=URL_OK, ordem=i))
        db.commit()
    return turma_id


def matricular_aluno(client, turma_id):
    r = client.get("/turmas-disponiveis")
    token = extrair_csrf(r.text)
    r = client.post(f"/turmas/{turma_id}/matricular", data={"csrf_token": token}, follow_redirects=False)
    assert r.headers["location"] == "/dashboard"


# ------------------------------------------------------------- RF05 ---------

def test_turma_sem_matricula_redireciona(client):
    turma_id = criar_turma_com_aulas(client)
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client)
    r = client.get(f"/turmas/{turma_id}", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (303, "/turmas-disponiveis")
    assert "Você não está matriculado" in client.get("/turmas-disponiveis").text


def test_turma_matriculado_mostra_aulas_e_player(client):
    turma_id = criar_turma_com_aulas(client)
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client)
    matricular_aluno(client, turma_id)

    r = client.get(f"/turmas/{turma_id}")
    assert r.status_code == 200
    assert "Intensivo ENEM" in r.text
    assert "Aula 1" in r.text and "Aula 2" in r.text
    assert "youtube.com/embed/dQw4w9WgXcQ" in r.text  # player
    assert "Marcar como concluída" in r.text


def test_concluir_aula_idempotente_e_indicador(client):
    turma_id = criar_turma_com_aulas(client, n_aulas=2)
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client)
    matricular_aluno(client, turma_id)

    # aula 1: id = menor id da turma
    with SessionLocal() as db:
        aula1 = db.query(Aula).filter(Aula.turma_id == turma_id).order_by(Aula.ordem).first().id

    r = client.get(f"/turmas/{turma_id}")
    token = extrair_csrf(r.text)
    r = client.post(f"/aulas/{aula1}/concluir", data={"csrf_token": token}, follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (303, f"/turmas/{turma_id}")

    # indicador verde + botão desabilitado na concluída; botão ativo na outra
    r = client.get(f"/turmas/{turma_id}")
    assert "✓ Concluída" in r.text
    assert "Marcar como concluída" in r.text  # só a aula 2 ainda tem botão

    # idempotente: concluir de novo não gera erro
    r = client.get(f"/turmas/{turma_id}")
    token = extrair_csrf(r.text)
    r = client.post(f"/aulas/{aula1}/concluir", data={"csrf_token": token}, follow_redirects=False)
    assert r.status_code == 303


def test_concluir_sem_matricula_flash_erro(client):
    turma_id = criar_turma_com_aulas(client)
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client)
    with SessionLocal() as db:
        aula_id = db.query(Aula).filter(Aula.turma_id == turma_id).first().id
    r = client.get("/dashboard")
    token = extrair_csrf(r.text)
    r = client.post(f"/aulas/{aula_id}/concluir", data={"csrf_token": token}, follow_redirects=False)
    assert r.status_code == 303
    assert "Você não está matriculado" in client.get("/dashboard").text


def test_progresso_atualiza_no_dashboard(client):
    turma_id = criar_turma_com_aulas(client, n_aulas=2)
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client)
    matricular_aluno(client, turma_id)

    with SessionLocal() as db:
        aula1 = db.query(Aula).filter(Aula.turma_id == turma_id).order_by(Aula.ordem).first().id
    r = client.get(f"/turmas/{turma_id}")
    token = extrair_csrf(r.text)
    client.post(f"/aulas/{aula1}/concluir", data={"csrf_token": token})

    r = client.get("/dashboard")
    assert "50%" in r.text and "1 de 2 aulas concluídas" in r.text


# ------------------------------------------------------------- RF07 ---------

def test_cronograma_exige_login(client):
    r = client.get("/cronograma/1", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (302, "/auth/login")


def test_cronograma_lista_aulas_em_ordem(client):
    turma_id = criar_turma_com_aulas(client, nome="Regular FUVEST", n_aulas=3)
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client)

    r = client.get(f"/cronograma/{turma_id}")
    assert r.status_code == 200
    assert "Cronograma" in r.text and "Regular FUVEST" in r.text
    # ordem 1., 2., 3. com títulos
    pos1 = r.text.index("1.")
    pos_a1 = r.text.index("Aula 1")
    assert pos1 < pos_a1 < r.text.index("Aula 2") < r.text.index("Aula 3")
    assert "Imprimir" in r.text


def test_cronograma_turma_inexistente(client):
    cadastrar_e_logar_aluno(client, email="crono@teste.com")
    r = client.get("/cronograma/99999", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (303, "/dashboard")
    assert "Turma não encontrada" in client.get("/dashboard").text
