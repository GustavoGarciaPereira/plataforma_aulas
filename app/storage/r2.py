"""Storage Cloudflare R2 (API compatível com S3) — ESQUELETO.

Não implementado de propósito. Quando for ativar:
  1. Adicionar `boto3` ao requirements.txt;
  2. Definir no ambiente: R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
     R2_ENDPOINT_URL (ex.: `https://<account_id>.r2.cloudflarestorage.com`)
     e R2_BUCKET;
  3. Setar `STORAGE_BACKEND=r2`;
  4. Implementar os métodos abaixo. Observações:
     - `salvar`: enviar os bytes com `s3.upload_fileobj(arquivo.file, bucket, chave)`;
     - `deletar`: `s3.delete_object(Bucket=bucket, Key=identificador)`;
     - `obter_path`: o R2 não tem caminho local — para servir, o ideal é
       devolver uma URL assinada (`generate_presigned_url`) e fazer a rota de
       download redirecionar (302) para ela, em vez de FileResponse;
     - a factory (`factory.get_storage()`) já levanta NotImplementedError
       enquanto este backend não estiver pronto.
"""

from pathlib import Path

from fastapi import UploadFile

from .base import StorageBackend


class R2Storage(StorageBackend):
    """Armazenamento em Cloudflare R2 (esqueleto — implementar na migração)."""

    def salvar(self, arquivo: UploadFile, subpasta: str) -> str:
        # TODO: validar via upload_validator e enviar ao bucket R2 com boto3.
        raise NotImplementedError("R2Storage.salvar ainda não foi implementado.")

    def deletar(self, identificador: str) -> bool:
        # TODO: s3.delete_object(Bucket=bucket, Key=identificador) -> True.
        raise NotImplementedError("R2Storage.deletar ainda não foi implementado.")

    def obter_path(self, identificador: str) -> Path:
        # TODO: gerar URL assinada do R2 (a rota de download faria redirect).
        raise NotImplementedError("R2Storage.obter_path ainda não foi implementado.")
