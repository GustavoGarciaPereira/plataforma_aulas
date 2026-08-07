"""Servir arquivos de upload (PDF/JPG/PNG) com controle de acesso por papel.

Permissão:
  - `propostas/`: professor dono da turma OU aluno matriculado na turma da aula;
  - `redacoes/`: professor dono da turma OU aluno dono da redação.

Não autorizado -> 404 (não revela a existência do arquivo). Anônimo -> login
(regra do `get_current_user`).
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..services.redacao_service import permitir_download_upload
from ..utils.upload import caminho_absoluto

router = APIRouter(tags=["uploads"], dependencies=[Depends(get_current_user)])


@router.get("/uploads/{caminho:path}")
def download_upload(request: Request, caminho: str, db: Session = Depends(get_db)):
    """Serve o arquivo se o usuário tem permissão; 404 caso contrário."""
    try:
        arquivo = caminho_absoluto(caminho)
    except ValueError:
        return Response(status_code=404)  # path traversal
    if not arquivo.is_file():
        return Response(status_code=404)
    if not permitir_download_upload(
        db, request.session["user_id"], request.session.get("role"), caminho
    ):
        return Response(status_code=404)
    return FileResponse(arquivo)
