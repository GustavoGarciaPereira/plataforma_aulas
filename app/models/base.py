"""Base declarativa e helpers compartilhados dos models."""

from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


def utcnow() -> datetime:
    """Datetime atual timezone-aware em UTC (evita ambiguidade de fuso)."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Classe base declarativa — todos os models herdam dela."""
