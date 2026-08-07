"""Models SQLAlchemy 2.0 — MVP Plataforma de Correção e Aulas de Redação.

Fonte: PRD v1.0 (seção 5.1, RF01–RF07; seção 8 — arquitetura; seção 13 — apêndice).
Ajustes técnicos aplicados em relação ao apêndice do PRD (ver análise):
  - `senha` virou `senha_hash` (nunca armazenar senha em texto puro);
  - `Turma.tipo` adicionado (exigido pelo RF02: intensivo/regular);
  - `Matricula.criada_em` adicionado (apoia RF06 — "últimas atividades");
  - UniqueConstraint em `(turma_id, ordem)`, `(aluno_id, turma_id)` e
    `(matricula_id, aula_id)` para impedir duplicidades (falhas técnicas do PRD).

Este pacote substitui o antigo `app/models.py` (arquivo único): cada entidade
vive em seu módulo e este `__init__` reexporta tudo para não quebrar imports
existentes (`from app.models import Base, Professor, Aluno, Turma, Aula,
Matricula, AulaConcluida, Redacao, Correcao`).
"""

from .aluno import Aluno
from .aula import Aula
from .aula_concluida import AulaConcluida
from .base import Base, utcnow
from .correcao import Correcao
from .matricula import Matricula
from .professor import Professor
from .redacao import Redacao
from .turma import Turma

__all__ = [
    "Aluno",
    "Aula",
    "AulaConcluida",
    "Base",
    "Correcao",
    "Matricula",
    "Professor",
    "Redacao",
    "Turma",
    "utcnow",
]
