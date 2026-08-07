"""E2E RF01 — autenticação (regressão do fix de CSRF/dependências)."""

from tests.conftest import extrair_csrf


def login(client, email, senha) -> None:
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    r = client.post(
        "/auth/login",
        data={"email": email, "senha": senha, "csrf_token": token},
        follow_redirects=False,
    )
    assert r.status_code == 303


def test_raiz_redireciona_anonimo(client):
    r = client.get("/", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (302, "/auth/login")


def test_cadastro_e_login_aluno(client):
    r = client.get("/auth/cadastro")
    token = extrair_csrf(r.text)
    r = client.post(
        "/auth/cadastro",
        data={
            "nome": "João Teste",
            "email": "joao@teste.com",
            "senha": "abc123",
            "confirmar_senha": "abc123",
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert (r.status_code, r.headers["location"]) == (303, "/auth/login")
    assert "Cadastro realizado com sucesso" in client.get("/auth/login").text

    login(client, "joao@teste.com", "abc123")
    assert client.get("/", follow_redirects=False).headers["location"] == "/dashboard"


def test_login_senha_errada_flash(client):
    login(client, "carla@exemplo.com", "errada")
    assert "Email ou senha inválidos" in client.get("/auth/login").text


def test_post_sem_csrf_rejeitado(client):
    """POST sem token CSRF não executa o login (flash de sessão expirada)."""
    r = client.post(
        "/auth/login",
        data={"email": "carla@exemplo.com", "senha": "123456"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "Sessão expirada" in client.get("/auth/login").text


def test_logout_limpa_sessao(client):
    login(client, "carla@exemplo.com", "123456")
    # / sempre redireciona o logado para /dashboard (main.py)
    assert client.get("/", follow_redirects=False).headers["location"] == "/dashboard"
    r = client.get("/auth/login")
    token = extrair_csrf(r.text)
    r = client.post("/auth/logout", data={"csrf_token": token}, follow_redirects=False)
    assert r.headers["location"] == "/auth/login"
    assert client.get("/", follow_redirects=False).headers["location"] == "/auth/login"
