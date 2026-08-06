"""Jinja2Templates compartilhado — evita import circular entre main.py e routers.

main.py e os routers importam ``templates`` daqui; os context processors
(usuário logado, mensagens flash, token CSRF) valem para todos os renders.
"""

from pathlib import Path

from starlette.routing import NoMatchFound
from starlette.templating import Jinja2Templates

from .utils.csrf import csrf_processor
from .utils.flash import mensagens_processor, usuario_processor

BASE_DIR = Path(__file__).resolve().parent.parent


def url_for_tolerante(request) -> dict:
    """Injeta ``url_for`` que retorna '#' quando a rota ainda não existe.

    Necessário enquanto os routers são criados incrementalmente (RF02–RF07):
    o nav do base.html referencia /dashboard e /turmas-disponiveis. Quando
    todas as rotas existirem, o fallback nunca dispara.
    """

    def url_for(name: str, **params) -> str:
        try:
            return request.url_for(name, **params)
        except NoMatchFound:
            return "#"

    return {"url_for": url_for}


templates = Jinja2Templates(
    directory=BASE_DIR / "app" / "templates",
    context_processors=[
        usuario_processor,
        mensagens_processor,
        csrf_processor,
        url_for_tolerante,  # por último: sobrescreve o url_for padrão
    ],
)
