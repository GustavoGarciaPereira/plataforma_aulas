"""Armazenamento de arquivos — interface e backends.

Prepara o projeto para migração futura ao Cloudflare R2 (API compatível com
S3) sem alterar services nem rotas: a camada de negócio depende apenas da
abstração `StorageBackend`, obtida via `app.storage.factory.get_storage()`.
"""
