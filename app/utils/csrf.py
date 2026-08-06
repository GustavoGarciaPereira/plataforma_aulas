"""CSRF — token de sessão para proteção dos formulários (PRD seção 6).

Uso:
  - o context processor ``csrf_processor`` injeta ``csrf_token`` em todo render;
  - os templates colocam o token num campo oculto dos <form method="post">;
  - os POSTs declaram ``dependencies=[Depends(verificar_csrf)]``.
"""

import secrets

from fastapi import Depends, Form, Request
from fastapi.responses import RedirectResponse

from .flash import flash

_CHAVE = "csrf_token"


def get_token_csrf(request: Request) -> str:
    """Retorna o token da sessão, criando-o se ainda não existir."""
    token = request.session.get(_CHAVE)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[_CHAVE] = token
    return token


def csrf_processor(request: Request) -> dict:
    """Injeta ``csrf_token`` no contexto dos templates."""
    return {"csrf_token": get_token_csrf(request)}


def verificar_csrf(request: Request, csrf_token: str = Form("")) -> None:
    """Dependência de POST: valida o token do form contra o da sessão.

    Falha → flash + redireciona de volta (referer) com 303. Comparação em
    tempo constante (secrets.compare_digest) para evitar timing attacks.
    """
    token_sessao = request.session.get(_CHAVE)
    if not token_sessao or not secrets.compare_digest(token_sessao, csrf_token):
        flash(request, "error", "Sessão expirada. Tente novamente.")
        destino = request.headers.get("referer") or "/"
        # Retorno (não raise) de uma Response interrompe a resolução da
        # dependência e é usado como resposta final — padrão FastAPI.
        return RedirectResponse(destino, status_code=303)
