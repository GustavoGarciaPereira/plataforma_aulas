"""Model Matricula — RF04 (vínculo aluno ↔ turma, gratuito no MVP)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, utcnow

if TYPE_CHECKING:
    from .aluno import Aluno
    from .aula_concluida import AulaConcluida
    from .turma import Turma


class Matricula(Base):
    """RF04 — vínculo aluno ↔ turma (gratuito no MVP; pago a partir da Semana 4)."""

    __tablename__ = "matriculas"
    __table_args__ = (
        # Fix técnico: impede matrícula duplicada do mesmo aluno na mesma turma.
        UniqueConstraint("aluno_id", "turma_id", name="uq_matricula_aluno_turma"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("alunos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    turma_id: Mapped[int] = mapped_column(
        ForeignKey("turmas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    aluno: Mapped["Aluno"] = relationship(back_populates="matriculas")
    turma: Mapped["Turma"] = relationship(back_populates="matriculas")
    concluidas: Mapped[list["AulaConcluida"]] = relationship(
        back_populates="matricula",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Matricula id={self.id} aluno={self.aluno_id} turma={self.turma_id}>"
