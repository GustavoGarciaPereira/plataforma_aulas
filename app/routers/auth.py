"""RF01 — Autenticação e cadastro. PRD v1.0, seção 5.1.

- Cadastro de aluno (nome, e-mail, senha) com hash bcrypt (app/security.py).
- Login de aluno e professor via sessão por cookie (user_id, role, nome).
- Logout via POST (protegido por CSRF — GET logout é vulnerável a CSRF).
- Todos os POSTs passam pela dependência verificar_csrf.
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Aluno, Professor
from ..security import hash_senha, verificar_senha
from ..templating import templates
from ..utils.csrf import verificar_csrf
from ..utils.flash import flash

router = APIRouter(prefix="/auth")


def _email_normalizado(email: str) -> str:
    """Normaliza e-mail (espaços/caixa) antes de consultar/gravar."""
    return email.strip().lower()


def _buscar_por_email(db: Session, email: str) -> tuple[Aluno | None, Professor | None]:
    """Busca aluno e professor com o mesmo e-mail (professor único na V1)."""
    aluno = db.query(Aluno).filter(Aluno.email == email).first()
    professor = db.query(Professor).filter(Professor.email == email).first()
    return aluno, professor


# ---------------------------------------------------------------- login ---

@router.get("/login")
def login(request: Request):
    return templates.TemplateResponse(request, "login.html", {})


@router.post("/login", dependencies=[Depends(verificar_csrf)])
def login_post(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        email = _email_normalizado(email)
        aluno, professor = _buscar_por_email(db, email)
        alvo = aluno or professor
        if alvo is None or not verificar_senha(senha, alvo.senha_hash):
            flash(request, "error", "Email ou senha inválidos.")
            return RedirectResponse("/auth/login", status_code=303)

        request.session["user_id"] = alvo.id
        request.session["role"] = "aluno" if aluno else "professor"
        request.session["nome"] = alvo.nome
        flash(request, "success", f"Bem-vindo(a), {alvo.nome}!")

        destino = "/dashboard" if aluno else "/professor/dashboard"
        return RedirectResponse(destino, status_code=303)
    except Exception:
        db.rollback()
        flash(request, "error", "Erro interno. Tente novamente.")
        return RedirectResponse("/auth/login", status_code=303)


# -------------------------------------------------------------- cadastro ---

@router.get("/cadastro")
def cadastro(request: Request):
    return templates.TemplateResponse(request, "cadastro.html", {})


@router.post("/cadastro", dependencies=[Depends(verificar_csrf)])
def cadastro_post(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    confirmar_senha: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        nome = nome.strip()
        email = _email_normalizado(email)

        if not nome or not email:
            flash(request, "error", "Preencha todos os campos.")
            return RedirectResponse("/auth/cadastro", status_code=303)
        if "@" not in email or "." not in email.split("@")[-1]:
            flash(request, "error", "E-mail inválido.")
            return RedirectResponse("/auth/cadastro", status_code=303)
        if senha != confirmar_senha:
            flash(request, "error", "As senhas não conferem.")
            return RedirectResponse("/auth/cadastro", status_code=303)

        aluno, professor = _buscar_por_email(db, email)
        if aluno or professor:
            flash(request, "error", "Este email já está cadastrado.")
            return RedirectResponse("/auth/cadastro", status_code=303)

        novo = Aluno(nome=nome, email=email, senha_hash=hash_senha(senha))
        db.add(novo)
        db.commit()

        flash(request, "success", "Cadastro realizado com sucesso! Faça login.")
        return RedirectResponse("/auth/login", status_code=303)
    except Exception:
        db.rollback()
        flash(request, "error", "Erro interno. Tente novamente.")
        return RedirectResponse("/auth/cadastro", status_code=303)


# ---------------------------------------------------------------- logout ---

@router.post("/logout", dependencies=[Depends(verificar_csrf)])
def logout(request: Request):
    request.session.clear()
    flash(request, "success", "Você saiu da sua conta.")
    return RedirectResponse("/auth/login", status_code=303)
