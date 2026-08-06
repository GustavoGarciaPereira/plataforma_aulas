"""Exceção de redirecionamento com flash — usada por dependências.

Dependências do FastAPI não devem "retornar" uma Response esperando
short-circuit: a partir da versão 0.141.x o retorno é ignorado como resposta
(o endpoint continua rodando). O padrão à prova de versão é lançar esta
exceção; o handler registrado em app/main.py converte em flash + redirect.
"""


class RedirecionarComFlash(Exception):
    """Redireciona com mensagem flash (categoria do base.html: success/error/info)."""

    def __init__(
        self,
        destino: str,
        categoria: str = "error",
        mensagem: str = "",
        status_code: int = 302,
    ):
        self.destino = destino
        self.categoria = categoria
        self.mensagem = mensagem
        self.status_code = status_code
        super().__init__(mensagem)
