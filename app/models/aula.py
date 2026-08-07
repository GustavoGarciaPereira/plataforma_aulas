"""Model Aula — RF03/RF05 (vídeo do YouTube com ordem numérica na turma)."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..utils.youtube import YouTubeURLError, embed_url_from_url
from .base import Base

if TYPE_CHECKING:
    from .aula_concluida import AulaConcluida
    from .redacao import Redacao
    from .turma import Turma


class Aula(Base):
    """RF03/RF05 — aula com vídeo do YouTube e ordem numérica dentro da turma."""

    __tablename__ = "aulas"
    __table_args__ = (
        # Fix técnico: impede duas aulas com a mesma ordem na mesma turma.
        UniqueConstraint("turma_id", "ordem", name="uq_aula_turma_ordem"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    turma_id: Mapped[int] = mapped_column(
        ForeignKey("turmas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    youtube_url: Mapped[str] = mapped_column(String(500), nullable=False)
    ordem: Mapped[int] = mapped_column(nullable=False)

    # Proposta de redação (RF08 — Semanas 2-3)
    tema: Mapped[str | None] = mapped_column(String(200), nullable=True)
    texto_apoio: Mapped[str | None] = mapped_column(Text, nullable=True)
    comando: Mapped[str | None] = mapped_column(Text, nullable=True)

    turma: Mapped["Turma"] = relationship(back_populates="aulas")
    concluidas: Mapped[list["AulaConcluida"]] = relationship(
        back_populates="aula",
        cascade="all, delete-orphan",
    )
    redacoes: Mapped[list["Redacao"]] = relationship(
        back_populates="aula",
        cascade="all, delete-orphan",
    )

    @property
    def embed_url(self) -> str | None:
        """URL de embed pronta para iframe (youtube-nocookie) ou None se inválida."""
        try:
            return embed_url_from_url(self.youtube_url)
        except YouTubeURLError:
            return None

    def __repr__(self) -> str:
        return f"<Aula id={self.id} ordem={self.ordem} titulo={self.titulo!r}>"
