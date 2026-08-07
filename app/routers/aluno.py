"""RF04/RF06 — Matrícula e progresso do aluno. PRD v1.0, seção 5.1.

Router fino: lógica em app/services/matricula_service.py; aqui ficam
respostas, flash e redirects. Todas as rotas exigem login (get_current_user).
"""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Aula, Matricula
from ..services.matricula_service import (
    calcular_progresso,
    concluir_aula,
    dados_dashboard,
    ja_matriculado,
    listar_aulas_para_aluno,
    matricular,
)
from ..services.matricula_service import (
    listar_turmas_disponiveis as listar_turmas_service,  # alias: o nome da rota é o mesmo
)
from ..services.redacao_service import (
    listar_redacoes_do_aluno,
    obter_dados_redacao_do_aluno,
    obter_redacao_com_correcao,
    submeter_redacao,
)
from ..templating import templates
from ..utils.csrf import verificar_csrf
from ..utils.flash import flash

router = APIRouter(tags=["aluno"], dependencies=[Depends(get_current_user)])


def _erro_redirect(request: Request, exc: Exception, destino: str) -> RedirectResponse:
    """ValueError -> flash da mensagem; RuntimeError -> flash genérico."""
    if isinstance(exc, ValueError):
        flash(request, "error", str(exc))
    else:
        flash(request, "error", "Erro interno. Tente novamente.")
    return RedirectResponse(destino, status_code=303)


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard do aluno (RF06); professora é redirecionada ao seu painel."""
    if request.session.get("role") == "professor":
        return RedirectResponse("/professor/dashboard", status_code=302)
    try:
        dados = dados_dashboard(db, request.session["user_id"])
    except RuntimeError as exc:
        return _erro_redirect(request, exc, "/dashboard")
    return templates.TemplateResponse(request, "dashboard.html", dados)


@router.get("/turmas-disponiveis")
def listar_turmas_disponiveis(request: Request, db: Session = Depends(get_db)):
    try:
        turmas = listar_turmas_service(db)
        aluno_id = request.session["user_id"]
        itens = [{"turma": t, "matriculado": ja_matriculado(db, aluno_id, t.id)} for t in turmas]
    except RuntimeError as exc:
        return _erro_redirect(request, exc, "/turmas-disponiveis")
    return templates.TemplateResponse(request, "turmas_disponiveis.html", {"itens": itens})


@router.post("/turmas/{turma_id}/matricular", dependencies=[Depends(verificar_csrf)])
def matricular_post(request: Request, turma_id: int, db: Session = Depends(get_db)):
    try:
        matricular(db, request.session["user_id"], turma_id)
        flash(request, "success", "Matrícula realizada! Bem-vindo(a) à turma.")
        return RedirectResponse("/dashboard", status_code=303)
    except (ValueError, RuntimeError) as exc:
        return _erro_redirect(request, exc, "/turmas-disponiveis")


# ---------------------------------------------------------------- RF05 ----


@router.get("/turmas/{turma_id}")
def turma_aluno(request: Request, turma_id: int, db: Session = Depends(get_db)):
    """Página da turma: lista de aulas com player e botão de conclusão."""
    try:
        dados = listar_aulas_para_aluno(db, turma_id, request.session["user_id"])
        progresso = calcular_progresso(db, turma_id, request.session["user_id"])
    except ValueError as exc:
        flash(request, "error", str(exc))
        return RedirectResponse("/turmas-disponiveis", status_code=303)
    except RuntimeError as exc:
        return _erro_redirect(request, exc, "/dashboard")
    dados["progresso"] = progresso
    return templates.TemplateResponse(request, "turma_aluno.html", dados)


@router.post("/aulas/{aula_id}/concluir", dependencies=[Depends(verificar_csrf)])
def concluir_post(request: Request, aula_id: int, db: Session = Depends(get_db)):
    """Marca a aula como concluída (idempotente). Matrícula resolvida pela
    turma da aula + aluno da sessão (não dá para concluir aula de outra turma)."""
    try:
        aula = db.get(Aula, aula_id)
        if aula is None:
            raise ValueError("Aula não encontrada.")
        matricula = (
            db.query(Matricula)
            .filter(
                Matricula.aluno_id == request.session["user_id"],
                Matricula.turma_id == aula.turma_id,
            )
            .first()
        )
        if matricula is None:
            raise ValueError("Você não está matriculado nesta turma.")
        concluir_aula(db, matricula.id, aula_id)
        flash(request, "success", "Aula concluída! 🎉")
        return RedirectResponse(f"/turmas/{aula.turma_id}", status_code=303)
    except (ValueError, RuntimeError) as exc:
        return _erro_redirect(request, exc, "/dashboard")


# ---------------------------------------------------------------- RF08 ----
# Submissão de redação, histórico e correção (Semanas 2-3).


@router.get("/turmas/{turma_id}/aulas/{aula_id}/redacao")
def redacao_pagina(request: Request, turma_id: int, aula_id: int, db: Session = Depends(get_db)):
    """Página da redação da aula: formulário de submissão ou a redação já enviada."""
    try:
        dados = obter_dados_redacao_do_aluno(db, request.session["user_id"], turma_id, aula_id)
    except (ValueError, RuntimeError) as exc:
        return _erro_redirect(request, exc, "/turmas-disponiveis")
    if dados["redacao"]:
        return templates.TemplateResponse(request, "ver_redacao.html", dados)
    return templates.TemplateResponse(request, "submeter_redacao.html", dados)


@router.post("/turmas/{turma_id}/aulas/{aula_id}/redacao", dependencies=[Depends(verificar_csrf)])
def redacao_submeter(
    request: Request,
    turma_id: int,
    aula_id: int,
    texto: str = Form(""),
    arquivo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Cria ou atualiza a redação do aluno (texto e/ou arquivo; reupload até corrigir)."""
    destino_erro = f"/turmas/{turma_id}/aulas/{aula_id}/redacao"
    try:
        dados = obter_dados_redacao_do_aluno(db, request.session["user_id"], turma_id, aula_id)
        submeter_redacao(db, dados["matricula"].id, aula_id, texto, arquivo)
        flash(request, "success", "Redação enviada com sucesso!")
        return RedirectResponse(destino_erro, status_code=303)
    except (ValueError, RuntimeError) as exc:
        return _erro_redirect(request, exc, destino_erro)


# ---------------------------------------------------------------- RF09 ----


@router.get("/redacoes")
def historico_redacoes(request: Request, db: Session = Depends(get_db)):
    """Histórico de redações do aluno (RF10)."""
    try:
        redacoes = listar_redacoes_do_aluno(db, request.session["user_id"])
    except RuntimeError as exc:
        return _erro_redirect(request, exc, "/dashboard")
    return templates.TemplateResponse(request, "historico_redacoes.html", {"redacoes": redacoes})


@router.get("/redacoes/{redacao_id}")
def ver_correcao(request: Request, redacao_id: int, db: Session = Depends(get_db)):
    """Detalhe da redação do aluno com a correção (se houver). Verifica propriedade."""
    try:
        redacao = obter_redacao_com_correcao(db, redacao_id, request.session["user_id"])
    except (ValueError, RuntimeError) as exc:
        return _erro_redirect(request, exc, "/redacoes")
    return templates.TemplateResponse(request, "ver_correcao.html", {"redacao": redacao})
