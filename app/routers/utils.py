"""RF07 — Cronograma para download/impressão. PRD v1.0, seção 5.1.

Exige login (qualquer usuário logado, sem verificar matrícula — facilita
professora e alunos). Renderiza HTML otimizado para impressão (@media print);
o PDF via WeasyPrint fica para worker (TODO, PRD seção 6).
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Turma
from ..services.aula_service import listar_aulas_da_turma
from ..templating import templates
from ..utils.flash import flash

router = APIRouter(tags=["utils"], dependencies=[Depends(get_current_user)])


@router.get("/cronograma/{turma_id}")
def cronograma(request: Request, turma_id: int, db: Session = Depends(get_db)):
    turma = db.get(Turma, turma_id)
    if turma is None:
        flash(request, "error", "Turma não encontrada.")
        return RedirectResponse("/dashboard", status_code=303)
    aulas = listar_aulas_da_turma(db, turma_id)
    return templates.TemplateResponse(
        request,
        "cronograma.html",
        {"turma": turma, "aulas": aulas, "now": datetime.now()},
    )
