"""Mensagens flash e contexto de usuário para os templates Jinja2.

Padrão: o router chama ``flash(request, categoria, texto)`` (ex.: após um POST)
e o context processor entrega ``mensagens`` e ``usuario`` em toda renderização,
limpando a sessão a cada request (o cookie da sessão fica pequeno).
"""

from starlette.requests import Request

# Categorias usadas no base.html: success | error | info


def flash(request: Request, categoria: str, texto: str) -> None:
    """Adiciona uma mensagem flash à sessão (exibida no próximo render)."""
    mensagens = request.session.setdefault("flash_messages", [])
    mensagens.append([categoria, texto])  # lista — sessão precisa ser JSON-serializável


def usuario_processor(request: Request) -> dict:
    """Injeta ``usuario`` no contexto: dict {id, nome, role} ou None (anônimo)."""
    if "user_id" not in request.session:
        return {"usuario": None}
    return {
        "usuario": {
            "id": request.session.get("user_id"),
            "nome": request.session.get("nome"),
            "role": request.session.get("role"),
        }
    }


def mensagens_processor(request: Request) -> dict:
    """Injeta ``mensagens`` (lista [categoria, texto]) e limpa a sessão."""
    mensagens = request.session.pop("flash_messages", None)
    return {"mensagens": mensagens or []}
