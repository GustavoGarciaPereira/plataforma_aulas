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

app = FastAPI(title="Plataforma de Redação")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=86400,      # 24h
    same_site="lax",
    # https_only=True   # habilitar em produção (HTTPS); em dev HTTP quebraria o cookie
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Estáticos (css/js/imagens próprios, se necessário)
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")

# --- Routers do MVP (RF01–RF07) ---
# TODO: descomentar conforme os arquivos forem criados em app/routers/.
from .routers import auth  # noqa: E402  # RF01

app.include_router(auth.router)
# from .routers import aluno, professor, turmas, utils
# app.include_router(professor.router)
# app.include_router(aluno.router)
# app.include_router(turmas.router)
# app.include_router(utils.router)


@app.get("/")
def home(request: Request) -> RedirectResponse:
    """Raiz: dashboard se logado, senão tela de login."""
    if "user_id" in request.session:
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/auth/login", status_code=302)
