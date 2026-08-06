"""RF02/RF03 — Gestão de turmas e aulas (professora). PRD v1.0, seção 5.1.

Router fino: toda a lógica de negócio vive em app/services/; aqui ficam
apenas validação de Form, montagem de resposta, flash e redirects.

Erros: ValueError -> flash com a mensagem amigável; RuntimeError -> flash
genérico. Todos os POSTs passam por verificar_csrf.
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_professor
from ..services.aula_service import (
    adicionar_aula,
    buscar_aula_da_professora,
    buscar_turma_do_professor,
    editar_aula,
    excluir_aula,
    listar_aulas_da_turma,
    mover_aula,
    reordenar_aulas,
)
from ..services.turma_service import (
    criar_turma,
    editar_turma,
    excluir_turma,
    listar_turmas_por_professor,
)
from ..templating import templates
from ..utils.csrf import verificar_csrf
from ..utils.flash import flash
from ..utils.youtube import YouTubeURLError, video_id_from_url

router = APIRouter(
    prefix="/professor",
    tags=["professor"],
    dependencies=[Depends(require_professor)],
)


# ------------------------------------------------------------- helpers ----

def _erro_redirect(request: Request, exc: Exception, destino: str) -> RedirectResponse:
    """ValueError -> flash da mensagem; RuntimeError -> flash genérico."""
    if isinstance(exc, ValueError):
        flash(request, "error", str(exc))
    else:
        flash(request, "error", "Erro interno. Tente novamente.")
    return RedirectResponse(destino, status_code=303)


def _miniatura(youtube_url: str) -> str | None:
    """Miniatura do vídeo (i.ytimg.com) ou None se URL inválida."""
    try:
        return f"https://i.ytimg.com/vi/{video_id_from_url(youtube_url)}/hqdefault.jpg"
    except YouTubeURLError:
        return None


# ---------------------------------------------------------------- RF02 ----

@router.get("/dashboard")
def dashboard_professor(request: Request, db: Session = Depends(get_db)):
    """Dashboard da professora: lista das suas turmas."""
    try:
        turmas = listar_turmas_por_professor(db, request.session["user_id"])
    except RuntimeError as exc:
        return _erro_redirect(request, exc, "/professor/dashboard")
    return templates.TemplateResponse(
        request, "professor_dashboard.html", {"turmas": turmas}
    )


@router.get("/turmas/nova")
def turma_nova(request: Request):
    return templates.TemplateResponse(request, "turma_form.html", {"turma": None})


@router.post("/turmas/nova", dependencies=[Depends(verificar_csrf)])
def turma_nova_post(
    request: Request,
    nome: str = Form(...),
    descricao: str = Form(""),
    tipo: str = Form("regular"),
    db: Session = Depends(get_db),
):
    try:
        criar_turma(db, request.session["user_id"], nome, descricao, tipo)
        flash(request, "success", "Turma criada com sucesso!")
        return RedirectResponse("/professor/dashboard", status_code=303)
    except (ValueError, RuntimeError) as exc:
        return _erro_redirect(request, exc, "/professor/turmas/nova")


@router.get("/turmas/{turma_id}/editar")
def turma_editar(request: Request, turma_id: int, db: Session = Depends(get_db)):
    try:
        turma = buscar_turma_do_professor(db, turma_id, request.session["user_id"])
    except ValueError as exc:
        return _erro_redirect(request, exc, "/professor/dashboard")
    return templates.TemplateResponse(
        request, "turma_form.html", {"turma": turma}
    )


@router.post("/turmas/{turma_id}/editar", dependencies=[Depends(verificar_csrf)])
def turma_editar_post(
    request: Request,
    turma_id: int,
    nome: str = Form(...),
    descricao: str = Form(""),
    tipo: str = Form("regular"),
    db: Session = Depends(get_db),
):
    try:
        editar_turma(
            db, turma_id, request.session["user_id"], nome, descricao, tipo
        )
        flash(request, "success", "Turma atualizada.")
        return RedirectResponse("/professor/dashboard", status_code=303)
    except (ValueError, RuntimeError) as exc:
        return _erro_redirect(request, exc, f"/professor/turmas/{turma_id}/editar")


@router.post("/turmas/{turma_id}/excluir", dependencies=[Depends(verificar_csrf)])
def turma_excluir(request: Request, turma_id: int, db: Session = Depends(get_db)):
    try:
        excluir_turma(db, turma_id, request.session["user_id"])
        flash(request, "success", "Turma excluída.")
    except (ValueError, RuntimeError) as exc:
        _erro_redirect(request, exc, "/professor/dashboard")
    return RedirectResponse("/professor/dashboard", status_code=303)


# ---------------------------------------------------------------- RF03 ----

@router.get("/turmas/{turma_id}/aulas")
def aulas_lista(request: Request, turma_id: int, db: Session = Depends(get_db)):
    try:
        turma = buscar_turma_do_professor(db, turma_id, request.session["user_id"])
        aulas = listar_aulas_da_turma(db, turma_id)
    except ValueError as exc:
        return _erro_redirect(request, exc, "/professor/dashboard")
    itens = [{"aula": aula, "thumbnail": _miniatura(aula.youtube_url)} for aula in aulas]
    return templates.TemplateResponse(
        request, "aulas_lista.html", {"turma": turma, "itens": itens}
    )


@router.get("/turmas/{turma_id}/aulas/nova")
def aula_nova(request: Request, turma_id: int, db: Session = Depends(get_db)):
    try:
        turma = buscar_turma_do_professor(db, turma_id, request.session["user_id"])
    except ValueError as exc:
        return _erro_redirect(request, exc, "/professor/dashboard")
    return templates.TemplateResponse(
        request, "aula_form.html", {"turma": turma, "aula": None}
    )


@router.post("/turmas/{turma_id}/aulas/nova", dependencies=[Depends(verificar_csrf)])
def aula_nova_post(
    request: Request,
    turma_id: int,
    titulo: str = Form(...),
    youtube_url: str = Form(...),
    ordem: str = Form(""),
    db: Session = Depends(get_db),
):
    destino_erro = f"/professor/turmas/{turma_id}/aulas/nova"
    ordem_raw = ordem.strip()
    if ordem_raw and not ordem_raw.isdigit():
        flash(request, "error", "Ordem deve ser um número.")
        return RedirectResponse(destino_erro, status_code=303)
    try:
        adicionar_aula(
            db,
            turma_id,
            request.session["user_id"],
            titulo,
            youtube_url,
            ordem=int(ordem_raw) if ordem_raw else None,
        )
        flash(request, "success", "Aula adicionada com sucesso!")
        return RedirectResponse(f"/professor/turmas/{turma_id}/aulas", status_code=303)
    except (ValueError, RuntimeError) as exc:
        return _erro_redirect(request, exc, destino_erro)


@router.get("/aulas/{aula_id}/editar")
def aula_editar(request: Request, aula_id: int, db: Session = Depends(get_db)):
    try:
        aula = buscar_aula_da_professora(db, aula_id, request.session["user_id"])
    except ValueError as exc:
        return _erro_redirect(request, exc, "/professor/dashboard")
    return templates.TemplateResponse(
        request, "aula_form.html", {"turma": aula.turma, "aula": aula}
    )


@router.post("/aulas/{aula_id}/editar", dependencies=[Depends(verificar_csrf)])
def aula_editar_post(
    request: Request,
    aula_id: int,
    titulo: str = Form(...),
    youtube_url: str = Form(...),
    ordem: str = Form(...),
    db: Session = Depends(get_db),
):
    destino_erro = f"/professor/aulas/{aula_id}/editar"
    if not ordem.strip().isdigit():
        flash(request, "error", "Ordem deve ser um número.")
        return RedirectResponse(destino_erro, status_code=303)
    try:
        aula = editar_aula(
            db, aula_id, request.session["user_id"], titulo, youtube_url, int(ordem)
        )
        flash(request, "success", "Aula atualizada.")
        return RedirectResponse(f"/professor/turmas/{aula.turma_id}/aulas", status_code=303)
    except (ValueError, RuntimeError) as exc:
        return _erro_redirect(request, exc, destino_erro)


@router.post("/aulas/{aula_id}/excluir", dependencies=[Depends(verificar_csrf)])
def aula_excluir(request: Request, aula_id: int, db: Session = Depends(get_db)):
    try:
        aula = buscar_aula_da_professora(db, aula_id, request.session["user_id"])
        excluir_aula(db, aula_id, request.session["user_id"])
        reordenar_aulas(db, aula.turma_id, request.session["user_id"])
        flash(request, "success", "Aula excluída.")
        return RedirectResponse(f"/professor/turmas/{aula.turma_id}/aulas", status_code=303)
    except (ValueError, RuntimeError) as exc:
        return _erro_redirect(request, exc, "/professor/dashboard")


@router.post("/aulas/{aula_id}/mover", dependencies=[Depends(verificar_csrf)])
def aula_mover(
    request: Request,
    aula_id: int,
    direcao: str = Form("cima"),
    db: Session = Depends(get_db),
):
    """Troca a ordem da aula com a adjacente (cima/baixo). Bônus RF03."""
    try:
        aula = buscar_aula_da_professora(db, aula_id, request.session["user_id"])
        moveu = mover_aula(db, aula_id, request.session["user_id"], direcao)
        if moveu:
            flash(request, "success", "Ordem atualizada.")
        else:
            flash(request, "info", "A aula já está no limite da lista.")
        return RedirectResponse(f"/professor/turmas/{aula.turma_id}/aulas", status_code=303)
    except (ValueError, RuntimeError) as exc:
        return _erro_redirect(request, exc, "/professor/dashboard")
