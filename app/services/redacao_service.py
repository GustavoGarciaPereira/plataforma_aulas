"""Camada de serviço — Redação e correção (RF08/RF09). PRD v1.0, seção 5.1.

Contrato de erros igual aos demais services:
  - ValueError: validação/propriedade com mensagem amigável;
  - RuntimeError: falha de banco (rollback aplicado aqui).
"""

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..models import Aula, Correcao, Matricula, Redacao, Turma
from ..storage.base import StorageBackend
from .aula_service import buscar_aula_da_professora
from .matricula_service import ja_matriculado
from .upload_service import substituir_upload

COMPETENCIAS = ("c1", "c2", "c3", "c4", "c5")
NOTA_MIN, NOTA_MAX = 0, 200


def _redacao_da_professora(db: Session, redacao_id: int, professor_id: int) -> Redacao:
    """Redação por id garantindo que pertence a uma turma da professora."""
    redacao = (
        db.query(Redacao)
        .join(Redacao.aula)
        .join(Aula.turma)
        .filter(Redacao.id == redacao_id, Turma.professor_id == professor_id)
        .first()
    )
    if redacao is None:
        raise ValueError("Redação não encontrada.")
    return redacao


def criar_proposta(
    db: Session,
    aula_id: int,
    professor_id: int,
    tema: str | None,
    texto_apoio: str | None,
    comando: str | None,
    arquivo: UploadFile | None = None,
    storage: StorageBackend | None = None,
) -> Aula:
    """Adiciona/atualiza a proposta de redação de uma aula (RF08). Verifica propriedade.

    `arquivo` opcional: salva via storage (default: get_storage()) em
    `uploads/propostas/` e substitui o anterior. A proposta da aula continua
    editável mesmo com redações já corrigidas.
    """
    try:
        aula = buscar_aula_da_professora(db, aula_id, professor_id)
        aula.tema = (tema or "").strip() or None
        aula.texto_apoio = (texto_apoio or "").strip() or None
        aula.comando = (comando or "").strip() or None
        if arquivo is not None:
            aula.proposta_arquivo = substituir_upload(
                storage, arquivo, "propostas", aula.proposta_arquivo
            )
        db.commit()
        db.refresh(aula)
        return aula
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao salvar proposta.") from exc


def listar_redacoes_pendentes(
    db: Session, professor_id: int, turma_id: int | None = None
) -> list[Redacao]:
    """Redações das turmas da professora (pendentes e corrigidas). Filtro opcional por turma."""
    try:
        query = (
            db.query(Redacao)
            .join(Redacao.aula)
            .join(Aula.turma)
            .filter(Turma.professor_id == professor_id)
        )
        if turma_id:
            query = query.filter(Aula.turma_id == turma_id)
        return query.order_by(Redacao.data_entrega.desc()).all()
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao listar redações.") from exc


def contar_redacoes_pendentes(db: Session, professor_id: int) -> int:
    """Nº de redações com status 'entregue' (aguardando correção) nas turmas da professora."""
    try:
        return (
            db.query(Redacao)
            .join(Redacao.aula)
            .join(Aula.turma)
            .filter(
                Turma.professor_id == professor_id,
                Redacao.status == "entregue",
            )
            .count()
        )
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao contar redações.") from exc


def obter_redacao_para_correcao(db: Session, redacao_id: int, professor_id: int) -> Redacao:
    """Redação por id para correção, garantindo propriedade da professora."""
    try:
        return _redacao_da_professora(db, redacao_id, professor_id)
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao buscar redação.") from exc


def corrigir_redacao(
    db: Session,
    redacao_id: int,
    professor_id: int,
    notas: dict[str, int],
    comentario_geral: str | None,
) -> Correcao:
    """Corrige uma redação com notas C1–C5 (0–200). Verifica propriedade e duplicidade."""
    try:
        redacao = _redacao_da_professora(db, redacao_id, professor_id)
        if redacao.correcao:
            raise ValueError("Esta redação já foi corrigida.")

        for comp in COMPETENCIAS:
            nota = notas.get(comp, 0)
            if not isinstance(nota, int) or not (NOTA_MIN <= nota <= NOTA_MAX):
                raise ValueError(f"Nota {comp.upper()} deve estar entre 0 e 200.")

        correcao = Correcao(
            redacao_id=redacao.id,
            nota_c1=notas.get("c1", 0),
            nota_c2=notas.get("c2", 0),
            nota_c3=notas.get("c3", 0),
            nota_c4=notas.get("c4", 0),
            nota_c5=notas.get("c5", 0),
            comentario_geral=(comentario_geral or "").strip() or None,
        )
        redacao.status = "corrigida"
        db.add(correcao)
        db.commit()
        db.refresh(correcao)
        return correcao
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao salvar correção.") from exc


def submeter_redacao(
    db: Session,
    matricula_id: int,
    aula_id: int,
    texto: str,
    arquivo: UploadFile | None = None,
    storage: StorageBackend | None = None,
) -> Redacao:
    """Cria ou atualiza a redação do aluno (RF08). Anti-trapaça: aula da turma da matrícula.

    - 1ª submissão exige texto OU arquivo;
    - antes da correção, o reupload substitui texto e/ou arquivo (via storage);
    - após corrigida, nada pode ser alterado.
    """
    try:
        matricula = db.get(Matricula, matricula_id)
        if matricula is None:
            raise ValueError("Matrícula não encontrada.")
        aula = (
            db.query(Aula).filter(Aula.id == aula_id, Aula.turma_id == matricula.turma_id).first()
        )
        if aula is None:
            raise ValueError("Aula não pertence à sua turma.")

        texto = (texto or "").strip()
        existente = (
            db.query(Redacao)
            .filter(Redacao.matricula_id == matricula_id, Redacao.aula_id == aula_id)
            .first()
        )
        if existente:
            if existente.status == "corrigida":
                raise ValueError("Esta redação já foi corrigida e não pode ser alterada.")
            if arquivo is not None:
                existente.arquivo_path = substituir_upload(
                    storage, arquivo, "redacoes", existente.arquivo_path
                )
            if texto:
                existente.texto = texto
            if not (existente.texto.strip() or existente.arquivo_path):
                raise ValueError("Informe o texto da redação ou anexe um arquivo.")
            db.commit()
            db.refresh(existente)
            return existente

        if not texto and arquivo is None:
            raise ValueError("Informe o texto da redação ou anexe um arquivo.")
        redacao = Redacao(matricula_id=matricula_id, aula_id=aula_id, texto=texto)
        if arquivo is not None:
            redacao.arquivo_path = substituir_upload(storage, arquivo, "redacoes", None)
        db.add(redacao)
        db.commit()
        db.refresh(redacao)
        return redacao
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao submeter redação.") from exc


def listar_redacoes_do_aluno(db: Session, aluno_id: int) -> list[Redacao]:
    """Redações do aluno (com correção, se existir), da mais recente para a mais antiga."""
    try:
        return (
            db.query(Redacao)
            .join(Redacao.matricula)
            .filter(Matricula.aluno_id == aluno_id)
            .order_by(Redacao.data_entrega.desc())
            .all()
        )
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao listar redações.") from exc


def obter_redacao_com_correcao(db: Session, redacao_id: int, aluno_id: int) -> Redacao:
    """Redação específica do aluno (com correção, se existir). Verifica propriedade."""
    try:
        redacao = (
            db.query(Redacao)
            .join(Redacao.matricula)
            .filter(Redacao.id == redacao_id, Matricula.aluno_id == aluno_id)
            .first()
        )
        if redacao is None:
            raise ValueError("Redação não encontrada.")
        return redacao
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao buscar redação.") from exc


def obter_dados_redacao_do_aluno(db: Session, aluno_id: int, turma_id: int, aula_id: int) -> dict:
    """Aula (com proposta) + redação já enviada, validando matrícula e propriedade.

    Devolve {"matricula": Matricula, "aula": Aula, "redacao": Redacao | None}.
    """
    try:
        matricula = (
            db.query(Matricula)
            .filter(Matricula.aluno_id == aluno_id, Matricula.turma_id == turma_id)
            .first()
        )
        if matricula is None:
            raise ValueError("Você não está matriculado nesta turma.")
        aula = db.get(Aula, aula_id)
        if aula is None or aula.turma_id != turma_id:
            raise ValueError("Aula não encontrada.")
        redacao = (
            db.query(Redacao)
            .filter(Redacao.matricula_id == matricula.id, Redacao.aula_id == aula_id)
            .first()
        )
        return {"matricula": matricula, "aula": aula, "redacao": redacao}
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao carregar a redação.") from exc


def permitir_download_upload(db: Session, usuario_id: int, role: str | None, caminho: str) -> bool:
    """Autoriza download de um arquivo de upload conforme o papel:

    - `propostas/`: professor dono da turma OU aluno matriculado nela;
    - `redacoes/`: professor dono da turma OU aluno dono da redação.

    Falha de banco nega o acesso (fail-closed) — a rota responde 404.
    """
    try:
        if caminho.startswith("propostas/"):
            aula = db.query(Aula).filter(Aula.proposta_arquivo == caminho).first()
            if aula is None:
                return False
            if role == "professor":
                return aula.turma.professor_id == usuario_id
            return ja_matriculado(db, usuario_id, aula.turma_id)
        if caminho.startswith("redacoes/"):
            redacao = db.query(Redacao).filter(Redacao.arquivo_path == caminho).first()
            if redacao is None:
                return False
            if role == "professor":
                return redacao.aula.turma.professor_id == usuario_id
            return redacao.matricula.aluno_id == usuario_id
        return False
    except Exception:
        db.rollback()
        return False
