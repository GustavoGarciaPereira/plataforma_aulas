"""Dependências reutilizáveis de autenticação/autorização.

- ``get_current_user``: exige sessão com user_id; senão flash + redirect ao login.
- ``require_professor``: exige role == 'professor'; senão flash + redirect ao dashboard.

Ambas LANÇAM RedirecionarComFlash (o handler em app/main.py converte em
flash + redirect) — retornar Response de dependência não interrompe o
endpoint no FastAPI 0.141+.
"""

from fastapi import Depends, Request

from .utils.redirecionar import RedirecionarComFlash


def get_current_user(request: Request) -> dict:
    """Retorna {user_id, role, nome} da sessão; redireciona ao login se anônimo."""
    user_id = request.session.get("user_id")
    if user_id is None:
        raise RedirecionarComFlash(
            "/auth/login", "info", "Faça login para continuar."
        )
    return {
        "user_id": user_id,
        "role": request.session.get("role"),
        "nome": request.session.get("nome"),
    }


def require_professor(request: Request, usuario: dict = Depends(get_current_user)) -> dict:
    """Como get_current_user, mas restringe a usuários com role 'professor'."""
    if usuario["role"] != "professor":
        raise RedirecionarComFlash(
            "/dashboard", "error", "Acesso restrito à professora."
        )
    return usuario
