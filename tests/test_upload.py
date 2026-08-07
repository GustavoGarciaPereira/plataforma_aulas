"""E2E upload de arquivos — proposta (professora) e redação (aluno)."""

from app.database import SessionLocal
from app.models import Aula, Correcao, Matricula, Redacao, Turma
from app.utils.upload import MAX_TAMANHO, RAIZ_UPLOADS
from tests.conftest import extrair_csrf

URL_YT_VALIDA = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

PDF_VALIDO = b"%PDF-1.4\n1 0 obj\n%%EOF"
PNG_VALIDO = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPG_VALIDO = b"\xff\xd8\xff\xe0" + b"\x00" * 32
EXE_FALSO = b"MZ\x90\x00" + b"\x00" * 64  # .exe renomeado para .pdf


def logar_professora(client):
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post(
        "/auth/login",
        data={"email": "carla@exemplo.com", "senha": "123456", "csrf_token": token},
    )


def cadastrar_e_logar_aluno(client, email="ana@teste.com"):
    r = client.get("/auth/cadastro")
    token = extrair_csrf(r.text)
    client.post(
        "/auth/cadastro",
        data={
            "nome": "Ana",
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


def criar_turma_e_aula(client) -> tuple[int, int]:
    """Turma + aula da Carla; devolve (turma_id, aula_id)."""
    logar_professora(client)
    r = client.get("/professor/turmas/nova")
    token = extrair_csrf(r.text)
    client.post(
        "/professor/turmas/nova",
        data={"nome": "Turma Upload", "descricao": "", "tipo": "regular", "csrf_token": token},
    )
    with SessionLocal() as db:
        turma_id = db.query(Turma).filter(Turma.nome == "Turma Upload").one().id
    r = client.get(f"/professor/turmas/{turma_id}/aulas/nova")
    token = extrair_csrf(r.text)
    client.post(
        f"/professor/turmas/{turma_id}/aulas/nova",
        data={"titulo": "Aula 1", "youtube_url": URL_YT_VALIDA, "ordem": "", "csrf_token": token},
    )
    with SessionLocal() as db:
        aula_id = db.query(Aula).filter(Aula.turma_id == turma_id).one().id
    return turma_id, aula_id


def matricular_aluno(client, turma_id: int) -> int:
    """Aluno entra na turma; devolve a matrícula id (aluno fica logado)."""
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client)
    r = client.get("/turmas-disponiveis")
    token = extrair_csrf(r.text)
    client.post(f"/turmas/{turma_id}/matricular", data={"csrf_token": token})
    with SessionLocal() as db:
        return db.query(Matricula).filter(Matricula.turma_id == turma_id).one().id


def _salvar_proposta_com_arquivo(client, turma_id, aula_id, nome, bytes_, content_type):
    r = client.get(f"/professor/turmas/{turma_id}/aulas/{aula_id}/proposta")
    token = extrair_csrf(r.text)
    return client.post(
        f"/professor/turmas/{turma_id}/aulas/{aula_id}/proposta",
        data={"tema": "Tema com arquivo", "texto_apoio": "", "comando": "", "csrf_token": token},
        files={"arquivo": (nome, bytes_, content_type)},
        follow_redirects=False,
    )


def _salvar_redacao_com_arquivo(client, turma_id, aula_id, nome, bytes_, content_type, texto=""):
    r = client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao")
    token = extrair_csrf(r.text)
    return client.post(
        f"/turmas/{turma_id}/aulas/{aula_id}/redacao",
        data={"texto": texto, "csrf_token": token},
        files={"arquivo": (nome, bytes_, content_type)},
        follow_redirects=False,
    )


# ------------------------------------------------------------ professor ---


def test_upload_pdf_na_proposta(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    r = _salvar_proposta_com_arquivo(
        client, turma_id, aula_id, "proposta.pdf", PDF_VALIDO, "application/pdf"
    )
    assert r.status_code == 303
    with SessionLocal() as db:
        aula = db.get(Aula, aula_id)
        assert aula.proposta_arquivo and aula.proposta_arquivo.startswith("propostas/")
        assert (RAIZ_UPLOADS / aula.proposta_arquivo).read_bytes() == PDF_VALIDO
    # form mostra o arquivo atual
    r = client.get(f"/professor/turmas/{turma_id}/aulas/{aula_id}/proposta")
    assert "Arquivo atual" in r.text and "/uploads/" in r.text


def test_rejeita_arquivo_invalido(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    r = _salvar_proposta_com_arquivo(
        client, turma_id, aula_id, "virus.exe.pdf", EXE_FALSO, "application/pdf"
    )
    assert r.headers["location"] == f"/professor/turmas/{turma_id}/aulas/{aula_id}/proposta"
    assert (
        "Formato inválido"
        in client.get(f"/professor/turmas/{turma_id}/aulas/{aula_id}/proposta").text
    )
    with SessionLocal() as db:
        assert db.get(Aula, aula_id).proposta_arquivo is None


def test_rejeita_arquivo_grande(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    grande = b"%PDF" + b"x" * (MAX_TAMANHO + 1)
    r = _salvar_proposta_com_arquivo(
        client, turma_id, aula_id, "grande.pdf", grande, "application/pdf"
    )
    assert r.headers["location"] == f"/professor/turmas/{turma_id}/aulas/{aula_id}/proposta"
    assert (
        "muito grande" in client.get(f"/professor/turmas/{turma_id}/aulas/{aula_id}/proposta").text
    )
    with SessionLocal() as db:
        assert db.get(Aula, aula_id).proposta_arquivo is None


# --------------------------------------------------------------- aluno ----


def test_upload_png_na_redacao(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    matricular_aluno(client, turma_id)
    r = _salvar_redacao_com_arquivo(
        client, turma_id, aula_id, "redacao.png", PNG_VALIDO, "image/png"
    )
    assert r.status_code == 303
    with SessionLocal() as db:
        redacao = db.query(Redacao).one()
        assert redacao.arquivo_path and redacao.arquivo_path.startswith("redacoes/")
        assert (RAIZ_UPLOADS / redacao.arquivo_path).read_bytes() == PNG_VALIDO


def test_redacao_sem_texto_e_sem_arquivo_rejeitada(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    matricular_aluno(client, turma_id)
    r = client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/turmas/{turma_id}/aulas/{aula_id}/redacao",
        data={"texto": "", "csrf_token": token},
        follow_redirects=False,
    )
    assert r.headers["location"] == f"/turmas/{turma_id}/aulas/{aula_id}/redacao"
    assert "Informe o texto" in client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao").text
    with SessionLocal() as db:
        assert db.query(Redacao).count() == 0


def test_substitui_arquivo_antes_da_correcao(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    matricular_aluno(client, turma_id)
    _salvar_redacao_com_arquivo(client, turma_id, aula_id, "v1.png", PNG_VALIDO, "image/png")
    with SessionLocal() as db:
        antigo = db.query(Redacao).one().arquivo_path
    assert (RAIZ_UPLOADS / antigo).is_file()

    _salvar_redacao_com_arquivo(client, turma_id, aula_id, "v2.pdf", PDF_VALIDO, "application/pdf")
    with SessionLocal() as db:
        novo = db.query(Redacao).one().arquivo_path
    assert novo != antigo and novo.endswith(".pdf")
    assert not (RAIZ_UPLOADS / antigo).exists()  # anterior removido do disco
    assert (RAIZ_UPLOADS / novo).read_bytes() == PDF_VALIDO


def test_bloqueia_upload_apos_correcao(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    matricular_aluno(client, turma_id)
    _salvar_redacao_com_arquivo(client, turma_id, aula_id, "v1.png", PNG_VALIDO, "image/png")
    with SessionLocal() as db:
        redacao = db.query(Redacao).one()
        redacao.status = "corrigida"
        db.add(
            Correcao(
                redacao_id=redacao.id,
                nota_c1=100,
                nota_c2=100,
                nota_c3=100,
                nota_c4=100,
                nota_c5=100,
            )
        )
        db.commit()
        caminho_antigo = redacao.arquivo_path

    r = _salvar_redacao_com_arquivo(
        client, turma_id, aula_id, "v2.pdf", PDF_VALIDO, "application/pdf"
    )
    assert r.headers["location"] == f"/turmas/{turma_id}/aulas/{aula_id}/redacao"
    assert "já foi corrigida" in client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao").text
    with SessionLocal() as db:
        assert db.query(Redacao).one().arquivo_path == caminho_antigo


# ------------------------------------------------------------- download ---


def test_download_proposta_dono_e_matriculado(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    _salvar_proposta_com_arquivo(
        client, turma_id, aula_id, "prop.pdf", PDF_VALIDO, "application/pdf"
    )
    with SessionLocal() as db:
        caminho = db.get(Aula, aula_id).proposta_arquivo

    # professora (dona) baixa
    r = client.get(f"/uploads/{caminho}")
    assert r.status_code == 200 and r.content == PDF_VALIDO

    # aluno matriculado baixa a proposta
    matricular_aluno(client, turma_id)
    r = client.get(f"/uploads/{caminho}")
    assert r.status_code == 200 and r.content == PDF_VALIDO

    # outro aluno (não matriculado) -> 404 (não revela existência)
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client, email="fora@teste.com")
    r = client.get(f"/uploads/{caminho}")
    assert r.status_code == 404

    # anônimo -> redirect para login
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    r = client.get(f"/uploads/{caminho}", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (302, "/auth/login")


def test_download_redacao_so_para_dono_e_professora(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    matricular_aluno(client, turma_id)  # Ana
    _salvar_redacao_com_arquivo(client, turma_id, aula_id, "r.png", PNG_VALIDO, "image/png")
    with SessionLocal() as db:
        caminho = db.query(Redacao).one().arquivo_path

    # Ana (dona) baixa
    r = client.get(f"/uploads/{caminho}")
    assert r.status_code == 200 and r.content == PNG_VALIDO

    # Bia (matriculada na mesma turma, mas não dona) -> 404
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client, email="bia@teste.com")
    r = client.get("/turmas-disponiveis")
    token = extrair_csrf(r.text)
    client.post(f"/turmas/{turma_id}/matricular", data={"csrf_token": token})
    r = client.get(f"/uploads/{caminho}")
    assert r.status_code == 404

    # professora (dona da turma) baixa
    logar_professora(client)
    r = client.get(f"/uploads/{caminho}")
    assert r.status_code == 200 and r.content == PNG_VALIDO
