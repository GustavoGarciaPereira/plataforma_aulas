"""Configuração da aplicação — carrega variáveis do arquivo .env (raiz do projeto).

PRD v1.0, seção 8: configuração por variáveis de ambiente (SECRET_KEY, DATABASE_URL).
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Raiz do projeto = diretório pai de app/ (onde fica o .env).
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Configurações da aplicação, sobrescrevíveis por variáveis de ambiente."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Conexão com o banco. Em produção, definir via .env / variável de ambiente.
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/plataforma_aulas"

    # Chave de assinatura das sessões (Starlette SessionMiddleware).
    # NUNCA use o valor padrão em produção: gere com `python -c "import secrets; print(secrets.token_hex(32))"`.
    secret_key: str = "dev-only-troque-no-env"

    # Backend de armazenamento de uploads: 'local' (disco) ou 'r2' (Cloudflare R2,
    # API compatível com S3 — ainda não implementado; ver app/storage/r2.py).
    storage_backend: str = "local"


settings = Settings()
