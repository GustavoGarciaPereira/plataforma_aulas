"""Camada de serviço — Turma (RF02). PRD v1.0, seção 5.1.

Contrato de erros:
  - ValueError: validação/propriedade com mensagem amigável (vira flash no router);
  - RuntimeError: falha de banco (rollback aplicado aqui; flash genérico no router).
"""

from sqlalchemy.orm import Session

from ..models import Turma

TIPOS_VALIDOS = ("intensivo", "regular", "outro")


def _validar(nome: str, tipo: str) -> str:
    """Valida e normaliza nome/tipo. Lança ValueError com mensagem amigável."""
    nome = (nome or "").strip()
    if not nome:
        raise ValueError("Informe o nome da turma.")
    if tipo not in TIPOS_VALIDOS:
        raise ValueError("Tipo de turma inválido.")
    return nome


def criar_turma(
    db: Session, professor_id: int, nome: str, descricao: str | None = None, tipo: str = "regular"
) -> Turma:
    try:
        nome = _validar(nome, tipo)
        turma = Turma(
            nome=nome,
            descricao=(descricao or "").strip(),
            tipo=tipo,
            professor_id=professor_id,
        )
        db.add(turma)
        db.commit()
        db.refresh(turma)
        return turma
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao criar turma.") from exc


def editar_turma(
    db: Session,
    turma_id: int,
    professor_id: int,
    nome: str,
    descricao: str | None = None,
    tipo: str = "regular",
) -> Turma:
    try:
        turma = db.get(Turma, turma_id)
        if turma is None or turma.professor_id != professor_id:
            raise ValueError("Turma não encontrada.")
        nome = _validar(nome, tipo)
        turma.nome = nome
        turma.descricao = (descricao or "").strip()
        turma.tipo = tipo
        db.commit()
        db.refresh(turma)
        return turma
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao editar turma.") from exc


def excluir_turma(db: Session, turma_id: int, professor_id: int) -> None:
    try:
        turma = db.get(Turma, turma_id)
        if turma is None or turma.professor_id != professor_id:
            raise ValueError("Turma não encontrada.")
        db.delete(turma)  # cascade "all, delete-orphan": aulas/matrículas somem
        db.commit()
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao excluir turma.") from exc


def listar_turmas_por_professor(db: Session, professor_id: int) -> list[Turma]:
    try:
        return db.query(Turma).filter(Turma.professor_id == professor_id).order_by(Turma.nome).all()
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao listar turmas.") from exc
