"""Model Professor — RF01 (professora Carla, única na V1)."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .turma import Turma


class Professor(Base):
    """RF01 — professora Carla, única na V1 (multi-professor é Semana 8+)."""

    __tablename__ = "professores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    turmas: Mapped[list["Turma"]] = relationship(
        back_populates="professor",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Professor id={self.id} email={self.email!r}>"
