"""Model Aluno — RF01 (aluno João, 16–22 anos, pré-vestibular)."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .matricula import Matricula


class Aluno(Base):
    """RF01 — aluno João (16–22 anos, pré-vestibular)."""

    __tablename__ = "alunos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    matriculas: Mapped[list["Matricula"]] = relationship(
        back_populates="aluno",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Aluno id={self.id} email={self.email!r}>"
