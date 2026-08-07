"""Camada de serviço — Aula (RF03). PRD v1.0, seção 5.1.

Contrato de erros (igual ao turma_service):
  - ValueError: validação/propriedade com mensagem amigável;
  - RuntimeError: falha de banco (rollback aplicado aqui).
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Aula, Turma
from ..utils.youtube import YouTubeURLError, video_id_from_url

# ------------------------------------------------------------ consultas ----


def buscar_turma_do_professor(db: Session, turma_id: int, professor_id: int) -> Turma:
    """Turma por id garantindo propriedade; senão ValueError."""
    turma = db.get(Turma, turma_id)
    if turma is None or turma.professor_id != professor_id:
        raise ValueError("Turma não encontrada.")
    return turma


def buscar_aula_da_professora(db: Session, aula_id: int, professor_id: int) -> Aula:
    """Aula por id garantindo que a turma pertence à professora; senão ValueError."""
    aula = db.get(Aula, aula_id)
    if aula is None or aula.turma.professor_id != professor_id:
        raise ValueError("Aula não encontrada.")
    return aula


def listar_aulas_da_turma(db: Session, turma_id: int) -> list[Aula]:
    """Aulas da turma em ordem crescente (ordem, id)."""
    return db.query(Aula).filter(Aula.turma_id == turma_id).order_by(Aula.ordem, Aula.id).all()


# --------------------------------------------------------------- escrita ----


def _validar_url(youtube_url: str) -> None:
    """Valida URL do YouTube; lança ValueError com mensagem amigável."""
    try:
        video_id_from_url(youtube_url)
    except YouTubeURLError:
        raise ValueError("URL do YouTube inválida.")


def adicionar_aula(
    db: Session,
    turma_id: int,
    professor_id: int,
    titulo: str,
    youtube_url: str,
    ordem: int | None = None,
) -> Aula:
    try:
        buscar_turma_do_professor(db, turma_id, professor_id)
        titulo = (titulo or "").strip()
        if not titulo:
            raise ValueError("Informe o título da aula.")
        _validar_url(youtube_url)

        if ordem is None:
            ordem = (
                db.query(func.max(Aula.ordem)).filter(Aula.turma_id == turma_id).scalar() or 0
            ) + 1
        else:
            duplicada = (
                db.query(Aula).filter(Aula.turma_id == turma_id, Aula.ordem == ordem).first()
            )
            if duplicada:
                raise ValueError("Já existe uma aula nesta posição (ordem).")

        aula = Aula(
            turma_id=turma_id,
            titulo=titulo,
            youtube_url=youtube_url.strip(),
            ordem=ordem,
        )
        db.add(aula)
        db.commit()
        db.refresh(aula)
        return aula
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao adicionar aula.") from exc


def editar_aula(
    db: Session,
    aula_id: int,
    professor_id: int,
    titulo: str,
    youtube_url: str,
    ordem: int,
) -> Aula:
    try:
        aula = buscar_aula_da_professora(db, aula_id, professor_id)
        titulo = (titulo or "").strip()
        if not titulo:
            raise ValueError("Informe o título da aula.")
        _validar_url(youtube_url)
        duplicada = (
            db.query(Aula)
            .filter(Aula.turma_id == aula.turma_id, Aula.ordem == ordem, Aula.id != aula.id)
            .first()
        )
        if duplicada:
            raise ValueError("Já existe uma aula nesta posição (ordem).")

        aula.titulo = titulo
        aula.youtube_url = youtube_url.strip()
        aula.ordem = ordem
        db.commit()
        db.refresh(aula)
        return aula
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao editar aula.") from exc


def excluir_aula(db: Session, aula_id: int, professor_id: int) -> None:
    try:
        aula = buscar_aula_da_professora(db, aula_id, professor_id)
        db.delete(aula)
        db.commit()
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao excluir aula.") from exc


def reordenar_aulas(db: Session, turma_id: int, professor_id: int) -> None:
    """Reenumera as aulas da turma em 1..n pela ordem atual (após exclusões)."""
    try:
        buscar_turma_do_professor(db, turma_id, professor_id)
        aulas = listar_aulas_da_turma(db, turma_id)
        for i, aula in enumerate(aulas, start=1):
            if aula.ordem != i:
                # Processando em ordem crescente, o destino i já foi liberado
                # ou está livre — flush a cada passo respeita o UNIQUE.
                aula.ordem = i
                db.flush()
        db.commit()
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao reordenar aulas.") from exc


def mover_aula(db: Session, aula_id: int, professor_id: int, direcao: str) -> bool:
    """Troca a ordem com a aula adjacente (cima/baixo). True se moveu."""
    try:
        aula = buscar_aula_da_professora(db, aula_id, professor_id)
        if direcao == "cima":
            adjacente = (
                db.query(Aula)
                .filter(Aula.turma_id == aula.turma_id, Aula.ordem < aula.ordem)
                .order_by(Aula.ordem.desc())
                .first()
            )
        else:
            adjacente = (
                db.query(Aula)
                .filter(Aula.turma_id == aula.turma_id, Aula.ordem > aula.ordem)
                .order_by(Aula.ordem.asc())
                .first()
            )
        if adjacente is None:
            return False

        # Troca em 3 passos com sentinela (-1): UPDATE único com CASE viola
        # UNIQUE(turma_id, ordem) no meio (SQLite/Postgres checam por linha).
        ordem_atual, ordem_adjacente = aula.ordem, adjacente.ordem
        aula.ordem = -1
        db.flush()
        adjacente.ordem = ordem_atual
        db.flush()
        aula.ordem = ordem_adjacente
        db.commit()
        return True
    except ValueError:
        raise
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Erro ao mover aula.") from exc
