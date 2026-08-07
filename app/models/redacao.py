"""Model Redacao — RF08 (redação entregue pelo aluno; status entregue/corrigida)."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, utcnow

if TYPE_CHECKING:
    from .aula import Aula
    from .correcao import Correcao
    from .matricula import Matricula


class Redacao(Base):
    """RF08 — redação submetida pelo aluno (uma por matrícula + aula)."""

    __tablename__ = "redacoes"
    __table_args__ = (
        # Fix técnico: impede o mesmo aluno entregar 2 redações para a mesma aula.
        UniqueConstraint("matricula_id", "aula_id", name="uq_redacao_matricula_aula"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    matricula_id: Mapped[int] = mapped_column(
        ForeignKey("matriculas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    aula_id: Mapped[int] = mapped_column(
        ForeignKey("aulas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    # Caminho relativo do arquivo enviado (uploads/redacoes/...), opcional
    arquivo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 'entregue' ou 'corrigida' (RF08/RF09)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="entregue")
    data_entrega: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    matricula: Mapped["Matricula"] = relationship(back_populates="redacoes")
    aula: Mapped["Aula"] = relationship(back_populates="redacoes")
    correcao: Mapped[Optional["Correcao"]] = relationship(
        back_populates="redacao",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Redacao id={self.id} aula={self.aula_id} status={self.status!r}>"
