"""Utilitários de URL do YouTube — extração do ID do vídeo e montagem do embed.

Usado pelo RF03: o professor cola qualquer link do YouTube e o sistema
converte automaticamente para o formato de iframe exibido ao aluno (RF05).

Formatos suportados:
    https://www.youtube.com/watch?v=ID
    https://youtu.be/ID
    https://www.youtube.com/embed/ID
    https://www.youtube.com/shorts/ID
    https://www.youtube.com/live/ID
    https://www.youtube.com/v/ID
    (inclui subdomínios como m. e music., com ou sem parâmetros extras:
    ?t=, &list=, ?si= — todos ignorados.)
"""

import re
from urllib.parse import parse_qs, urlparse

# ID de vídeo do YouTube: exatamente 11 caracteres [A-Za-z0-9_-].
_VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")

# Hosts considerados de vídeo do YouTube (youtu.be é o encurtador oficial).
_HOSTS_VIDEO = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtube-nocookie.com",
    "youtu.be",
}


class YouTubeURLError(ValueError):
    """URL do YouTube inválida ou sem ID de vídeo extraível."""


def video_id_from_url(url: str) -> str:
    """Extrai e devolve o ID do vídeo de uma URL do YouTube.

    Levanta ``YouTubeURLError`` (subclasse de ``ValueError``) quando a URL
    é vazia, não é do YouTube ou não contém um ID válido. O router deve
    capturar a exceção e exibir a mensagem ao professor (ex.: mensagem flash).
    """
    if not url or not isinstance(url, str):
        raise YouTubeURLError("A URL do vídeo não pode ser vazia.")

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        # Tolerância: professor cola o link sem o protocolo.
        url = "https://" + url

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    if host not in _HOSTS_VIDEO:
        raise YouTubeURLError(
            f'A URL "{url}" não é do YouTube (domínio: {host or "desconhecido"}).'
        )

    video_id: str | None = None

    if host == "youtu.be":
        # https://youtu.be/ID?si=...
        video_id = parsed.path.lstrip("/").split("/")[0] or None
    elif parsed.path.rstrip("/") == "/watch" or parsed.path.startswith("/watch"):
        # https://www.youtube.com/watch?v=ID&t=30
        video_id = parse_qs(parsed.query).get("v", [None])[0]
    else:
        # https://www.youtube.com/{embed|shorts|live|v}/ID
        partes = [p for p in parsed.path.split("/") if p]
        if partes and partes[0] in ("embed", "shorts", "live", "v"):
            video_id = partes[1] if len(partes) > 1 else None

    if video_id and _VIDEO_ID_PATTERN.fullmatch(video_id):
        return video_id

    raise YouTubeURLError(f'Não foi possível extrair o ID do vídeo da URL: "{url}".')


def embed_url_from_url(url: str) -> str:
    """Converte uma URL do YouTube em URL de embed pronta para o iframe.

    Usa o domínio canônico www.youtube.com/embed (máxima compatibilidade:
    youtube-nocookie.com exibe "Video unavailable" em algumas regiões/redes,
    mesmo com vídeos válidos). Para priorizar privacidade, troque para
    "https://www.youtube-nocookie.com/embed/{id}?rel=0".
    """
    video_id = video_id_from_url(url)
    return f"https://www.youtube.com/embed/{video_id}?rel=0"
