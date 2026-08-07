"""Aplicação FastAPI — Plataforma de Redação (PRD v1.0, seção 8).

- Sessões por cookie assinado (Starlette SessionMiddleware), autenticação
  guarda apenas user_id / role / nome na sessão.
- Templates via app/templating.py (context processors: usuário, flash, CSRF).
- Estáticos de app/static/.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .templating import templates  # noqa: F401  # inicializa os templates
from .utils.flash import flash
from .utils.redirecionar import RedirecionarComFlash

app = FastAPI(title="Plataforma de Redação")


@app.exception_handler(RedirecionarComFlash)
async def redirecionar_com_flash(request: Request, exc: RedirecionarComFlash):
    """Converte RedirecionarComFlash (de dependências) em flash + redirect."""
    flash(request, exc.categoria, exc.mensagem)
    return RedirectResponse(exc.destino, status_code=exc.status_code)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=86400,  # 24h
    same_site="lax",
    # https_only=True   # habilitar em produção (HTTPS); em dev HTTP quebraria o cookie
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Estáticos (css/js/imagens próprios, se necessário)
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")

# --- Routers do MVP (RF01–RF07) ---
# TODO: descomentar conforme os arquivos forem criados em app/routers/.
from .routers import (
    aluno,  # RF04/RF05/RF06 (dashboard, matrícula, turma)
    auth,  # RF01
    professor,  # RF02/RF03
    utils,  # RF07 (cronograma)
)

app.include_router(auth.router)
app.include_router(professor.router)
app.include_router(aluno.router)
app.include_router(utils.router)
# from .routers import turmas


@app.get("/")
def home(request: Request) -> RedirectResponse:
    """Raiz: dashboard se logado, senão tela de login."""
    if "user_id" in request.session:
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/auth/login", status_code=302)
