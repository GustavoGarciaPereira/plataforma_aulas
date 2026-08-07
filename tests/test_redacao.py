"""E2E RF08/RF09 — proposta de redação e correção pela professora (TestClient)."""

from app.database import SessionLocal
from app.models import Aula, Correcao, Matricula, Redacao, Turma
from tests.conftest import extrair_csrf

URL_YT_VALIDA = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


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
        data={"nome": "Turma Redação", "descricao": "", "tipo": "regular", "csrf_token": token},
    )
    with SessionLocal() as db:
        turma_id = db.query(Turma).filter(Turma.nome == "Turma Redação").one().id
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
    """Aluno entra na turma; devolve a matrícula id."""
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client)
    r = client.get("/turmas-disponiveis")
    token = extrair_csrf(r.text)
    client.post(f"/turmas/{turma_id}/matricular", data={"csrf_token": token})
    with SessionLocal() as db:
        return db.query(Matricula).filter(Matricula.turma_id == turma_id).one().id


def submeter_redacao(
    matricula_id: int, aula_id: int, texto: str = "Minha redação sobre o tema."
) -> int:
    """Insere redação direto no banco (rota do aluno é o próximo prompt)."""
    with SessionLocal() as db:
        redacao = Redacao(matricula_id=matricula_id, aula_id=aula_id, texto=texto)
        db.add(redacao)
        db.commit()
        db.refresh(redacao)
        return redacao.id


# ---------------------------------------------------------------- RF08 ---


def test_form_proposta_renderiza(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    r = client.get(f"/professor/turmas/{turma_id}/aulas/{aula_id}/proposta")
    assert r.status_code == 200
    assert "Proposta de Redação" in r.text
    assert 'name="csrf_token"' in r.text
    assert 'name="tema"' in r.text and 'name="texto_apoio"' in r.text and 'name="comando"' in r.text


def test_salvar_proposta_atualiza_aula_e_preenche_form(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    r = client.get(f"/professor/turmas/{turma_id}/aulas/{aula_id}/proposta")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/professor/turmas/{turma_id}/aulas/{aula_id}/proposta",
        data={
            "tema": "Os desafios da educação",
            "texto_apoio": "Texto motivador 1.\nTexto motivador 2.",
            "comando": "Disserte sobre o tema em até 30 linhas.",
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert (r.status_code, r.headers["location"]) == (303, f"/professor/turmas/{turma_id}/aulas")
    with SessionLocal() as db:
        aula = db.get(Aula, aula_id)
        assert aula.tema == "Os desafios da educação"
        assert aula.texto_apoio == "Texto motivador 1.\nTexto motivador 2."
        assert aula.comando == "Disserte sobre o tema em até 30 linhas."
    # edição: form volta preenchido
    r = client.get(f"/professor/turmas/{turma_id}/aulas/{aula_id}/proposta")
    assert 'value="Os desafios da educação"' in r.text
    assert "Disserte sobre o tema em até 30 linhas." in r.text


def test_proposta_de_aula_de_outra_turma_e_rejeitada(client):
    _, aula_id = criar_turma_e_aula(client)
    r = client.get(f"/professor/turmas/99999/aulas/{aula_id}/proposta", follow_redirects=False)
    assert r.headers["location"] == "/professor/dashboard"


# ---------------------------------------------------------------- RF09 ---


def test_lista_redacoes_e_correcao_completa(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    matricula_id = matricular_aluno(client, turma_id)
    redacao_id = submeter_redacao(matricula_id, aula_id)
    logar_professora(client)

    # lista mostra a redação pendente (aluno, turma, tema, botão Corrigir)
    r = client.get("/professor/redacoes")
    assert r.status_code == 200
    assert "Ana" in r.text and "Turma Redação" in r.text and "Pendente" in r.text
    assert f"/professor/redacoes/{redacao_id}/corrigir" in r.text

    # formulário de correção com o texto da redação e campos C1-C5
    r = client.get(f"/professor/redacoes/{redacao_id}/corrigir")
    assert r.status_code == 200
    assert "Minha redação sobre o tema." in r.text
    assert 'name="nota_c1"' in r.text and 'name="comentario_geral"' in r.text

    # salvar correção
    token = extrair_csrf(r.text)
    r = client.post(
        f"/professor/redacoes/{redacao_id}/corrigir",
        data={
            "nota_c1": "180",
            "nota_c2": "160",
            "nota_c3": "140",
            "nota_c4": "120",
            "nota_c5": "100",
            "comentario_geral": "Bom texto, mas falta aprofundar.",
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert (r.status_code, r.headers["location"]) == (303, "/professor/redacoes")
    with SessionLocal() as db:
        redacao = db.get(Redacao, redacao_id)
        assert redacao.status == "corrigida"
        correcao = redacao.correcao
        assert correcao is not None
        assert (correcao.nota_c1, correcao.nota_c5) == (180, 100)
        assert correcao.comentario_geral == "Bom texto, mas falta aprofundar."

    # lista agora mostra "Corrigida" + ver correção preenche campos desabilitados
    r = client.get("/professor/redacoes")
    assert "Corrigida" in r.text
    r = client.get(f"/professor/redacoes/{redacao_id}/corrigir")
    assert 'value="180"' in r.text
    assert "Bom texto, mas falta aprofundar." in r.text
    assert "Total:" in r.text and "700/1000" in r.text


def test_nao_corrigir_duas_vezes(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    matricula_id = matricular_aluno(client, turma_id)
    redacao_id = submeter_redacao(matricula_id, aula_id)
    logar_professora(client)

    r = client.get(f"/professor/redacoes/{redacao_id}/corrigir")
    token = extrair_csrf(r.text)
    dados = {f"nota_{c}": "100" for c in ("c1", "c2", "c3", "c4", "c5")}
    dados["csrf_token"] = token
    client.post(f"/professor/redacoes/{redacao_id}/corrigir", data=dados)

    r = client.get(f"/professor/redacoes/{redacao_id}/corrigir")
    token = extrair_csrf(r.text)
    dados["csrf_token"] = token
    r = client.post(
        f"/professor/redacoes/{redacao_id}/corrigir", data=dados, follow_redirects=False
    )
    assert r.headers["location"] == f"/professor/redacoes/{redacao_id}/corrigir"
    assert "já foi corrigida" in client.get(f"/professor/redacoes/{redacao_id}/corrigir").text


def test_nota_invalida_nao_salva(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    matricula_id = matricular_aluno(client, turma_id)
    redacao_id = submeter_redacao(matricula_id, aula_id)
    logar_professora(client)

    r = client.get(f"/professor/redacoes/{redacao_id}/corrigir")
    token = extrair_csrf(r.text)
    dados = {f"nota_{c}": "100" for c in ("c1", "c2", "c3", "c4", "c5")}
    dados["nota_c1"] = "abc"
    dados["csrf_token"] = token
    r = client.post(
        f"/professor/redacoes/{redacao_id}/corrigir", data=dados, follow_redirects=False
    )
    assert r.headers["location"] == f"/professor/redacoes/{redacao_id}/corrigir"
    assert "deve ser um número" in client.get(f"/professor/redacoes/{redacao_id}/corrigir").text
    with SessionLocal() as db:
        assert db.get(Redacao, redacao_id).status == "entregue"


# --------------------------------------------------------- RF08 (aluno) ---


def _cenario_com_proposta(client) -> tuple[int, int, int]:
    """Turma + aula com proposta de redação + aluno matriculado (e logado)."""
    turma_id, aula_id = criar_turma_e_aula(client)
    matricula_id = matricular_aluno(client, turma_id)
    with SessionLocal() as db:
        aula = db.get(Aula, aula_id)
        aula.tema = "Os desafios da educação"
        aula.texto_apoio = "Texto motivador."
        aula.comando = "Disserte sobre o tema em até 30 linhas."
        db.commit()
    return turma_id, aula_id, matricula_id


def test_aluno_ve_formulario_de_submissao(client):
    turma_id, aula_id, _ = _cenario_com_proposta(client)
    r = client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao")
    assert r.status_code == 200
    assert "Enviar Redação" in r.text
    assert "Os desafios da educação" in r.text
    assert "Disserte sobre o tema em até 30 linhas." in r.text
    assert 'name="texto"' in r.text and 'name="csrf_token"' in r.text


def test_aluno_submete_redacao_e_ve_confirmacao(client):
    turma_id, aula_id, _ = _cenario_com_proposta(client)
    r = client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/turmas/{turma_id}/aulas/{aula_id}/redacao",
        data={"texto": "Minha dissertação sobre educação.", "csrf_token": token},
        follow_redirects=False,
    )
    assert r.headers["location"] == f"/turmas/{turma_id}/aulas/{aula_id}/redacao"
    # página agora mostra a redação enviada (badge Entregue)
    r = client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao")
    assert "Minha Redação" in r.text and "Entregue" in r.text
    assert "Minha dissertação sobre educação." in r.text
    with SessionLocal() as db:
        redacao = db.query(Redacao).one()
        assert redacao.status == "entregue"
        assert redacao.texto == "Minha dissertação sobre educação."


def test_aluno_nao_submete_duplicada(client):
    turma_id, aula_id, _ = _cenario_com_proposta(client)
    r = client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao")
    token = extrair_csrf(r.text)
    client.post(
        f"/turmas/{turma_id}/aulas/{aula_id}/redacao",
        data={"texto": "Primeira versão.", "csrf_token": token},
    )
    r = client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/turmas/{turma_id}/aulas/{aula_id}/redacao",
        data={"texto": "Segunda versão.", "csrf_token": token},
        follow_redirects=False,
    )
    assert r.headers["location"] == f"/turmas/{turma_id}/aulas/{aula_id}/redacao"
    assert (
        "Você já enviou sua redação"
        in client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao").text
    )
    with SessionLocal() as db:
        assert db.query(Redacao).count() == 1


def test_aluno_ve_historico(client):
    turma_id, aula_id, _ = _cenario_com_proposta(client)
    r = client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao")
    token = extrair_csrf(r.text)
    client.post(
        f"/turmas/{turma_id}/aulas/{aula_id}/redacao",
        data={"texto": "Redação do histórico.", "csrf_token": token},
    )
    r = client.get("/redacoes")
    assert r.status_code == 200
    assert "Minhas Redações" in r.text
    assert "Os desafios da educação" in r.text
    assert "Entregue" in r.text


def test_aluno_ve_correcao(client):
    turma_id, aula_id, matricula_id = _cenario_com_proposta(client)
    redacao_id = submeter_redacao(matricula_id, aula_id, "Texto para correção.")
    with SessionLocal() as db:
        redacao = db.get(Redacao, redacao_id)
        redacao.status = "corrigida"
        db.add(
            Correcao(
                redacao_id=redacao_id,
                nota_c1=200,
                nota_c2=180,
                nota_c3=160,
                nota_c4=140,
                nota_c5=120,
                comentario_geral="Excelente argumentação!",
            )
        )
        db.commit()

    r = client.get(f"/redacoes/{redacao_id}")
    assert r.status_code == 200
    assert "Os desafios da educação" in r.text
    assert "Texto para correção." in r.text
    assert "Excelente argumentação!" in r.text
    assert "800/1000" in r.text  # 200+180+160+140+120

    # página da redação na turma também mostra a correção
    r = client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao")
    assert "Corrigida" in r.text and "800/1000" in r.text


def test_aluno_nao_ve_correcao_de_outro_aluno(client):
    _, aula_id, matricula_id = _cenario_com_proposta(client)
    redacao_id = submeter_redacao(matricula_id, aula_id, "Redação da Ana.")
    with SessionLocal() as db:
        redacao = db.get(Redacao, redacao_id)
        redacao.status = "corrigida"
        db.add(
            Correcao(
                redacao_id=redacao_id,
                nota_c1=100,
                nota_c2=100,
                nota_c3=100,
                nota_c4=100,
                nota_c5=100,
            )
        )
        db.commit()

    # outro aluno (Bia) tenta acessar a correção da Ana
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client, email="bia@teste.com")
    r = client.get(f"/redacoes/{redacao_id}", follow_redirects=False)
    assert r.headers["location"] == "/redacoes"
    assert "Redação não encontrada." in client.get("/redacoes").text


def test_aluno_sem_matricula_redirecionado(client):
    turma_id, aula_id = criar_turma_e_aula(client)
    # aluno cadastrado/logado mas NÃO matriculado na turma
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    client.post("/auth/logout", data={"csrf_token": token})
    cadastrar_e_logar_aluno(client, email="cida@teste.com")

    r = client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao", follow_redirects=False)
    assert r.headers["location"] == "/turmas-disponiveis"
    assert "Você não está matriculado nesta turma." in client.get("/turmas-disponiveis").text

    # POST também é bloqueado
    r = client.get("/turmas-disponiveis")
    token = extrair_csrf(r.text)
    r = client.post(
        f"/turmas/{turma_id}/aulas/{aula_id}/redacao",
        data={"texto": "x", "csrf_token": token},
        follow_redirects=False,
    )
    assert r.headers["location"] == f"/turmas/{turma_id}/aulas/{aula_id}/redacao"
    assert (
        "Você não está matriculado nesta turma."
        in client.get(f"/turmas/{turma_id}/aulas/{aula_id}/redacao").text
    )
