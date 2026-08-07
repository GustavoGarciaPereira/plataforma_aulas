"""Model Correcao — RF09 (correção por competências C1–C5, 0–200 cada)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, utcnow

if TYPE_CHECKING:
    from .redacao import Redacao


class Correcao(Base):
    """RF09 — correção da professora: notas C1–C5 (0–200) + comentário geral."""

    __tablename__ = "correcoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    redacao_id: Mapped[int] = mapped_column(
        ForeignKey("redacoes.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    nota_c1: Mapped[int] = mapped_column(nullable=False, default=0)  # 0-200
    nota_c2: Mapped[int] = mapped_column(nullable=False, default=0)  # 0-200
    nota_c3: Mapped[int] = mapped_column(nullable=False, default=0)  # 0-200
    nota_c4: Mapped[int] = mapped_column(nullable=False, default=0)  # 0-200
    nota_c5: Mapped[int] = mapped_column(nullable=False, default=0)  # 0-200
    comentario_geral: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_correcao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    redacao: Mapped["Redacao"] = relationship(back_populates="correcao")

    def __repr__(self) -> str:
        return f"<Correcao id={self.id} redacao={self.redacao_id}>"
