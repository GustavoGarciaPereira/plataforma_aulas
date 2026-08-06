"""Dependências reutilizáveis de autenticação/autorização.

- ``get_current_user``: exige sessão com user_id; senão flash + redirect ao login.
- ``require_professor``: exige role == 'professor'; senão flash + redirect ao dashboard.
"""

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse

from .utils.flash import flash


def get_current_user(request: Request) -> dict | None:
    """Retorna {user_id, role, nome} da sessão; redireciona ao login se anônimo."""
    user_id = request.session.get("user_id")
    if user_id is None:
        flash(request, "info", "Faça login para continuar.")
        # Retorno (não raise) de uma Response interrompe a dependência e é
        # usado como resposta final — padrão FastAPI.
        return RedirectResponse("/auth/login", status_code=302)
    return {
        "user_id": user_id,
        "role": request.session.get("role"),
        "nome": request.session.get("nome"),
    }


def require_professor(
    request: Request, usuario: dict = Depends(get_current_user)
) -> dict:
    """Como get_current_user, mas restringe a usuários com role 'professor'."""
    if usuario["role"] != "professor":
        flash(request, "error", "Acesso restrito à professora.")
        return RedirectResponse("/dashboard", status_code=302)
    return usuario
