"""init — cria as 6 tabelas do MVP (PRD v1.0, seção 5.1 / 13).

Gerada a partir do Base.metadata (app.models). Equivale ao que o
`alembic revision --autogenerate -m "init"` produziria; quando houver um
Postgres disponível, rode `alembic upgrade head` para aplicar.
"""

import sqlalchemy as sa
from alembic import op

revision = "1a2b3c4d5e6f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "professores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_professores_email", "professores", ["email"], unique=True)

    op.create_table(
        "alunos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alunos_email", "alunos", ["email"], unique=True)

    op.create_table(
        "turmas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column(
            "professor_id",
            sa.Integer(),
            sa.ForeignKey("professores.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_turmas_professor_id", "turmas", ["professor_id"], unique=False)

    op.create_table(
        "aulas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "turma_id",
            sa.Integer(),
            sa.ForeignKey("turmas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("youtube_url", sa.String(length=500), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("turma_id", "ordem", name="uq_aula_turma_ordem"),
    )
    op.create_index("ix_aulas_turma_id", "aulas", ["turma_id"], unique=False)

    op.create_table(
        "matriculas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "aluno_id",
            sa.Integer(),
            sa.ForeignKey("alunos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "turma_id",
            sa.Integer(),
            sa.ForeignKey("turmas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aluno_id", "turma_id", name="uq_matricula_aluno_turma"),
    )
    op.create_index("ix_matriculas_aluno_id", "matriculas", ["aluno_id"], unique=False)
    op.create_index("ix_matriculas_turma_id", "matriculas", ["turma_id"], unique=False)

    op.create_table(
        "aulas_concluidas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "matricula_id",
            sa.Integer(),
            sa.ForeignKey("matriculas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "aula_id",
            sa.Integer(),
            sa.ForeignKey("aulas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("concluida_em", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("matricula_id", "aula_id", name="uq_concluida_matricula_aula"),
    )
    op.create_index(
        "ix_aulas_concluidas_matricula_id", "aulas_concluidas", ["matricula_id"], unique=False
    )
    op.create_index(
        "ix_aulas_concluidas_aula_id", "aulas_concluidas", ["aula_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("aulas_concluidas")
    op.drop_table("matriculas")
    op.drop_table("aulas")
    op.drop_table("turmas")
    op.drop_table("alunos")
    op.drop_table("professores")
