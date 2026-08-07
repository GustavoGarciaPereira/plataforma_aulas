"""Seed do professor padrão (RF01) — idempotente. PRD v1.0, seções 5.1 e 13.

Uso (a partir da raiz do projeto):
    venv/bin/python -m app.seed

Antes: aplicar as migrações com `venv/bin/alembic upgrade head`.
"""

import os
import sys
from pathlib import Path

# Bootstrap: permite rodar como `python -m app.seed` ou `python app/seed.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.exc import OperationalError, ProgrammingError

from app.database import SessionLocal
from app.models import Professor
from app.security import hash_senha

# Senha padrão do seed. Em produção, defina SEED_PROFESSOR_SENHA — nunca use
# a padrão fora de desenvolvimento.
SENHA_PADRAO = os.environ.get("SEED_PROFESSOR_SENHA", "123456")

EMAIL_PROFESSOR_PADRAO = "carla@exemplo.com"


def main() -> None:
    with SessionLocal() as db:
        existe = db.query(Professor).filter(Professor.email == EMAIL_PROFESSOR_PADRAO).first()
        if existe:
            print(
                f"Seed ignorado: professor {existe.email!r} já existe "
                f"(id={existe.id}). Nada a fazer."
            )
            return

        professor = Professor(
            nome="Carla",
            email=EMAIL_PROFESSOR_PADRAO,
            senha_hash=hash_senha(SENHA_PADRAO),
        )
        db.add(professor)
        db.commit()
        db.refresh(professor)
        print(f"Professor padrão criado: {professor.nome} <{professor.email}> (id={professor.id}).")


if __name__ == "__main__":
    try:
        main()
    except (ProgrammingError, OperationalError) as exc:
        # Diagnóstico rápido: tabelas ausentes (banco não migrado) ou conexão.
        msg = str(exc).lower()
        if "no such table" in msg or "does not exist" in msg:
            print(
                "ERRO: as tabelas ainda não existem. Execute antes:\n"
                "    venv/bin/alembic upgrade head"
            )
        else:
            print(
                "ERRO: não foi possível acessar o banco. Confira se o Postgres "
                "está no ar e o DATABASE_URL (app/config.py ou .env)."
            )
        print(f"Detalhe: {exc}")
        sys.exit(1)
