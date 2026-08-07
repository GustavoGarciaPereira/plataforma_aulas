"""Model AulaConcluida — RF05/RF06 (registro de conclusão de aula por matrícula)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, utcnow

if TYPE_CHECKING:
    from .aula import Aula
    from .matricula import Matricula


class AulaConcluida(Base):
    """RF05/RF06 — registro de conclusão de uma aula por uma matrícula."""

    __tablename__ = "aulas_concluidas"
    __table_args__ = (
        # Fix técnico: impede concluir a mesma aula 2x na mesma matrícula
        # (evita barra de progresso > 100%).
        UniqueConstraint("matricula_id", "aula_id", name="uq_concluida_matricula_aula"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    matricula_id: Mapped[int] = mapped_column(
        ForeignKey("matriculas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    aula_id: Mapped[int] = mapped_column(
        ForeignKey("aulas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concluida_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    matricula: Mapped["Matricula"] = relationship(back_populates="concluidas")
    aula: Mapped["Aula"] = relationship(back_populates="concluidas")

    def __repr__(self) -> str:
        return f"<AulaConcluida matricula={self.matricula_id} aula={self.aula_id}>"
