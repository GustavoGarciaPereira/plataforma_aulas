"""Model Turma — RF02 (turma criada pela professora, ex.: "Intensivo ENEM")."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .aula import Aula
    from .matricula import Matricula
    from .professor import Professor


class Turma(Base):
    """RF02 — turma criada pela professora (ex.: "Intensivo ENEM")."""

    __tablename__ = "turmas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="regular")
    professor_id: Mapped[int] = mapped_column(
        ForeignKey("professores.id", ondelete="CASCADE"), nullable=False, index=True
    )

    professor: Mapped["Professor"] = relationship(back_populates="turmas")
    aulas: Mapped[list["Aula"]] = relationship(
        back_populates="turma",
        cascade="all, delete-orphan",
        order_by="Aula.ordem",  # RF03/RF05: lista sempre em ordem
    )
    matriculas: Mapped[list["Matricula"]] = relationship(
        back_populates="turma",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Turma id={self.id} nome={self.nome!r}>"
