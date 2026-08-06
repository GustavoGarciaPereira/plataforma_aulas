"""Camada de serviço — Matrícula e progresso (RF04/RF06). PRD v1.0, seção 5.1.

Contrato de erros igual aos demais services:
  - ValueError: validação/propriedade com mensagem amigável;
  - RuntimeError: falha de banco (rollback aplicado aqui).
"""

from sqlalchemy.orm import Session

from ..models import Aula, AulaConcluida, Matricula, Turma


def listar_turmas_disponiveis(db: Session) -> list[Turma]:
    """Todas as turmas (ordem alfabética) para a tela de matrícula."""
    try:
        return db.query(Turma).order_by(Turma.nome).all()
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao listar turmas.") from exc


def ja_matriculado(db: Session, aluno_id: int, turma_id: int) -> bool:
    return (
        db.query(Matricula)
        .filter(Matricula.aluno_id == aluno_id, Matricula.turma_id == turma_id)
        .first()
        is not None
    )


def matricular(db: Session, aluno_id: int, turma_id: int) -> Matricula:
    """Cria a matrícula (idempotente: se já existe, devolve a atual)."""
    try:
        turma = db.get(Turma, turma_id)
        if turma is None:
            raise ValueError("Turma não encontrada.")
        existente = (
            db.query(Matricula)
            .filter(Matricula.aluno_id == aluno_id, Matricula.turma_id == turma_id)
            .first()
        )
        if existente:
            return existente
        matricula = Matricula(aluno_id=aluno_id, turma_id=turma_id)
        db.add(matricula)
        db.commit()
        db.refresh(matricula)
        return matricula
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao realizar matrícula.") from exc


def dados_dashboard(db: Session, aluno_id: int) -> dict:
    """Dados do dashboard do aluno (RF06): turmas + progresso + últimas conclusões."""
    try:
        matriculas = (
            db.query(Matricula).filter(Matricula.aluno_id == aluno_id).all()
        )
        turmas = []
        for m in matriculas:
            total = db.query(Aula).filter(Aula.turma_id == m.turma_id).count()
            concluidas = (
                db.query(AulaConcluida)
                .filter(AulaConcluida.matricula_id == m.id)
                .count()
            )
            turmas.append(
                {
                    "matricula_id": m.id,
                    "turma": m.turma,
                    "total_aulas": total,
                    "aulas_concluidas": concluidas,
                    "percentual": round(concluidas / total * 100) if total else 0,
                }
            )
        ultimas = (
            db.query(AulaConcluida)
            .join(Matricula, AulaConcluida.matricula_id == Matricula.id)
            .filter(Matricula.aluno_id == aluno_id)
            .order_by(AulaConcluida.concluida_em.desc())
            .limit(5)
            .all()
        )
        return {"turmas": turmas, "ultimas_concluidas": ultimas}
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao montar o dashboard.") from exc
