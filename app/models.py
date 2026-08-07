"""Models SQLAlchemy 2.0 — MVP Plataforma de Correção e Aulas de Redação.

Fonte: PRD v1.0 (seção 5.1, RF01–RF07; seção 8 — arquitetura; seção 13 — apêndice).
Ajustes técnicos aplicados em relação ao apêndice do PRD (ver análise):
  - `senha` virou `senha_hash` (nunca armazenar senha em texto puro);
  - `Turma.tipo` adicionado (exigido pelo RF02: intensivo/regular);
  - `Matricula.criada_em` adicionado (apoia RF06 — "últimas atividades");
  - UniqueConstraint em `(turma_id, ordem)`, `(aluno_id, turma_id)` e
    `(matricula_id, aula_id)` para impedir duplicidades (falhas técnicas do PRD).
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .utils.youtube import YouTubeURLError, embed_url_from_url


def utcnow() -> datetime:
    """Datetime atual timezone-aware em UTC (evita ambiguidade de fuso)."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Classe base declarativa — todos os models herdam dela."""


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

    turma: Mapped["Turma"] = relationship(back_populates="aulas")
    concluidas: Mapped[list["AulaConcluida"]] = relationship(
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
