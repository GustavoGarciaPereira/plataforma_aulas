"""CSRF — token de sessão para proteção dos formulários (PRD seção 6).

Uso:
  - o context processor ``csrf_processor`` injeta ``csrf_token`` em todo render;
  - os templates colocam o token num campo oculto dos <form method="post">;
  - os POSTs declaram ``dependencies=[Depends(verificar_csrf)]``.
"""

import secrets

from fastapi import Form, Request

from .redirecionar import RedirecionarComFlash

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

    Falha → RedirecionarComFlash (handler em main.py faz flash + redirect de
    volta com 303). Comparação em tempo constante (secrets.compare_digest).
    """
    token_sessao = request.session.get(_CHAVE)
    if not token_sessao or not secrets.compare_digest(token_sessao, csrf_token):
        destino = request.headers.get("referer") or "/"
        raise RedirecionarComFlash(
            destino, "error", "Sessão expirada. Tente novamente.", status_code=303
        )
