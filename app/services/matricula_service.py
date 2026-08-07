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
        matriculas = db.query(Matricula).filter(Matricula.aluno_id == aluno_id).all()
        turmas = []
        for m in matriculas:
            total = db.query(Aula).filter(Aula.turma_id == m.turma_id).count()
            concluidas = db.query(AulaConcluida).filter(AulaConcluida.matricula_id == m.id).count()
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


# ------------------------------------------------------------ RF05/RF06 ----


def concluir_aula(db: Session, matricula_id: int, aula_id: int) -> AulaConcluida | None:
    """Registra conclusão de aula (RF05). Idempotente: None se já existia.

    Anti-trapaça: a aula precisa pertencer à turma da matrícula.
    """
    try:
        matricula = db.get(Matricula, matricula_id)
        if matricula is None:
            raise ValueError("Matrícula não encontrada.")
        aula = db.get(Aula, aula_id)
        if aula is None or aula.turma_id != matricula.turma_id:
            raise ValueError("Aula não pertence a esta turma.")

        existente = (
            db.query(AulaConcluida)
            .filter(
                AulaConcluida.matricula_id == matricula_id,
                AulaConcluida.aula_id == aula_id,
            )
            .first()
        )
        if existente:
            return None  # já concluída — nada a fazer

        conclusao = AulaConcluida(matricula_id=matricula_id, aula_id=aula_id)
        db.add(conclusao)
        db.commit()
        db.refresh(conclusao)
        return conclusao
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao concluir aula.") from exc


def listar_aulas_para_aluno(db: Session, turma_id: int, aluno_id: int) -> dict:
    """Aulas da turma para o aluno matriculado (RF05): dicts com embed e status.

    Lança ValueError "Você não está matriculado nesta turma." se não matriculado.
    """
    try:
        matricula = (
            db.query(Matricula)
            .filter(Matricula.aluno_id == aluno_id, Matricula.turma_id == turma_id)
            .first()
        )
        if matricula is None:
            raise ValueError("Você não está matriculado nesta turma.")

        turma = db.get(Turma, turma_id)
        aulas = db.query(Aula).filter(Aula.turma_id == turma_id).order_by(Aula.ordem, Aula.id).all()
        concluidas = {
            c.aula_id
            for c in db.query(AulaConcluida)
            .filter(AulaConcluida.matricula_id == matricula.id)
            .all()
        }
        itens = [
            {
                "id": a.id,
                "titulo": a.titulo,
                "ordem": a.ordem,
                "embed_url": a.embed_url,
                "concluida": a.id in concluidas,
            }
            for a in aulas
        ]
        return {"turma": turma, "aulas": itens}
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao listar aulas.") from exc


def calcular_progresso(db: Session, turma_id: int, aluno_id: int) -> dict:
    """Progresso do aluno numa turma (RF06): {total, concluidas, percentual}."""
    try:
        matricula = (
            db.query(Matricula)
            .filter(Matricula.aluno_id == aluno_id, Matricula.turma_id == turma_id)
            .first()
        )
        if matricula is None:
            raise ValueError("Você não está matriculado nesta turma.")
        total = db.query(Aula).filter(Aula.turma_id == turma_id).count()
        concluidas = (
            db.query(AulaConcluida).filter(AulaConcluida.matricula_id == matricula.id).count()
        )
        return {
            "total": total,
            "concluidas": concluidas,
            "percentual": round(concluidas / total * 100) if total else 0,
        }
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao calcular progresso.") from exc
