"""Segurança — hash de senhas com bcrypt (passlib CryptContext).

PRD v1.0, seção 6: "Senhas hash (bcrypt)". Usado pelo seed (app/seed.py) e
pelos routers de autenticação (RF01).
"""

from passlib.context import CryptContext

# deprecated="auto" avisa se o esquema padrão ficar obsoleto.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    """Gera o hash bcrypt de uma senha em texto puro."""
    return pwd_context.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Confere senha em texto puro contra o hash armazenado."""
    return pwd_context.verify(senha, senha_hash)
