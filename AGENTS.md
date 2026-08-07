# AGENTS.md — Plataforma de Redação (MVP Semana 1 + Redação RF08–RF10)

Memória persistente do projeto: qualquer agente/desenvolvedor retoma daqui. Estado atualizado ao final do MVP da Semana 1 e da fase Redação (Semanas 2-3).

## Project

Plataforma web para professora de redação publicar trilhas de aulas (vídeos do YouTube), alunos se matricularem, assistirem e acompanharem progresso; correção de redações (RF08–RF10) implementada. Persona principal: professora **Carla** (`carla@exemplo.com`, seed).

**Stack:** Python 3.12 · FastAPI (server-side) · Jinja2 · SQLAlchemy 2.0 · Alembic · PostgreSQL (produção) / **SQLite** (dev, `dev.db`) · Tailwind CSS via CDN · Starlette sessions (cookie assinado).

- Entry point: `app/main.py` (app `Plataforma de Redação`)

## Commands

```bash
cd ~/plataforma_aulas
venv/bin/python -m venv venv                # já criado (Python 3.12)
venv/bin/pip install -r requirements.txt    # runtime
venv/bin/pip install -r requirements-dev.txt  # pytest, httpx
venv/bin/uvicorn app.main:app --reload      # servidor dev (porta 8000)
venv/bin/python -m pytest tests/ -q         # suíte (81 testes)
venv/bin/ruff check .                       # lint (config: ruff.toml)
venv/bin/ruff format .                      # formatação (estilo Black)
venv/bin/alembic upgrade head               # migrações
venv/bin/python -m app.seed                 # seed da professora Carla (idempotente)
```

## Architecture

- `app/main.py` — app, SessionMiddleware, handler `RedirecionarComFlash`, inclui routers.
- `app/routers/` — **finos**: `auth.py` (/auth), `professor.py` (/professor, RF02/03/08/09), `aluno.py` (RF04–06 e RF08–10), `utils.py` (/cronograma, RF07), `uploads.py` (download protegido de arquivos). Lógica de negócio NUNCA no router.
- `app/services/` — `turma_service.py`, `aula_service.py`, `matricula_service.py`, `redacao_service.py`, `upload_service.py`: validam e persistem; erros: `ValueError` (mensagem amigável → flash) e `RuntimeError` (rollback + flash genérico).
- `app/storage/` — abstração de armazenamento de uploads: `base.py` (interface `StorageBackend`), `local.py` (`LocalStorage`, disco em `uploads/`), `r2.py` (esqueleto Cloudflare R2), `factory.py` (`get_storage()` por `STORAGE_BACKEND`, default `local`). Services recebem storage injetado (default: factory); validação fica em `upload_validator.py`.
- `app/models/` — pacote com um módulo por entidade: `base.py` (`Base` + `utcnow`), `professor.py`, `aluno.py`, `turma.py`, `aula.py`, `matricula.py`, `aula_concluida.py`, `redacao.py`, `correcao.py`; o `__init__.py` reexporta tudo, então `from app.models import ...` continua funcionando como antes.
- `app/templating.py` — `Jinja2Templates` compartilhado + context processors (`usuario`, `mensagens` flash, `csrf_token`, `url_for` tolerante → `#` se rota não existe).
- `app/utils/` — `youtube.py` (extração de ID + embed), `csrf.py`, `flash.py`, `redirecionar.py`, `upload_validator.py` (magic bytes PDF/JPG/PNG + tamanho ≤10MB).
- `app/dependencies.py` — `get_current_user` (login obrigatório), `require_professor` (role professor); lançam `RedirecionarComFlash`.
- `tests/` — E2E TestClient + SQLite temporário (`conftest.py` seta `DATABASE_URL` antes dos imports; banco limpo por teste).

## Database

Models no pacote `app/models/` (Base = `DeclarativeBase`, em `base.py`; `__init__.py` reexporta tudo):

- `Professor(id, nome, email unique, senha_hash)` → turmas
- `Aluno(id, nome, email unique, senha_hash)` → matriculas
- `Turma(id, nome, descricao, tipo: intensivo|regular|outro, professor_id FK)` → aulas, matriculas
- `Aula(id, turma_id FK, titulo, youtube_url, ordem, tema?, texto_apoio?, comando?, proposta_arquivo?)` — property `embed_url`; `UNIQUE(turma_id, ordem)`; proposta da redação (RF08) com arquivo opcional
- `Matricula(id, aluno_id FK, turma_id FK, criada_em)` — `UNIQUE(aluno_id, turma_id)`
- `AulaConcluida(id, matricula_id FK, aula_id FK, concluida_em)` — `UNIQUE(matricula_id, aula_id)`
- `Redacao(id, matricula_id FK, aula_id FK, texto, arquivo_path?, status: entregue|corrigida, data_entrega)` — `UNIQUE(matricula_id, aula_id)`
- `Correcao(id, redacao_id FK unique, nota_c1..nota_c5 (0-200), comentario_geral?, data_correcao)` — 1:1 com Redacao (`uselist=False`)

Migrações Alembic `1a2b3c4d5e6f` (init), `68348fb2d833` (redação: `Redacao`/`Correcao` + proposta em `Aula`) e `bf4fe48c4206` (upload: `Aula.proposta_arquivo` + `Redacao.arquivo_path`). **Estado atual do `dev.db`** (set/2026): 1 professora (Carla), 3 turmas (TURMA 1 regular 2 aulas, TURMA 2 intensivo 2 aulas, TURMA 3 regular 1 aula), 5 aulas, 2 alunos, 3 matrículas (aluno2→T1, aluno2→T2, aluno3→T1); tabelas `redacoes`/`correcoes` e colunas de upload criadas pelas migrações (vazias); pasta `uploads/` local (ignorada pelo git, exceto `.gitkeep`).

## Features (MVP Semana 1 — RF01 a RF07 ✅)

- **RF01** Autenticação: cadastro aluno, login aluno/professora, logout POST, sessão + CSRF.
- **RF02** CRUD de turmas (só dona; tipo com select validação server-side).
- **RF03** CRUD de aulas: URL YouTube validada, ordem automática `MAX(ordem)+1`, mover ↑↓, duplicidade rejeitada, embed + miniatura.
- **RF04** Matrícula: turmas disponíveis + "Entrar na turma" idempotente.
- **RF05** Página da turma: player embed, "Marcar como concluída" idempotente e anti-trapaça, badge ✓.
- **RF06** Dashboard: turmas + barra de progresso (%) + últimas concluídas; nav por papel.
- **RF07** Cronograma: HTML `@media print` + botão Imprimir (PDF WeasyPrint: pendente).

## Features (Semanas 2-3 — RF08 a RF10 ✅)

- **RF08** Proposta de redação: professora anexa tema/texto_apoio/comando + arquivo opcional à aula (`/professor/turmas/{id}/aulas/{id}/proposta`); aluno envia redação em textarea e/ou arquivo (exige texto OU arquivo; PDF/JPG/PNG ≤10MB) — uma por matrícula+aula; **reupload** (texto e/ou arquivo) permitido até a correção; botão "Enviar Redação" na página da turma quando há proposta.
- **RF09** Correção: lista de redações com filtro por turma e contador de pendentes no dashboard da professora; notas C1–C5 (0–200) + comentário geral; correção única (duplicada → erro amigável); arquivo da redação e proposta disponíveis para download na página de correção.
- **RF10** Histórico: aluno vê minhas redações (`/redacoes`) e detalhe com tabela C1–C5, total /1000 e comentário (`/redacoes/{id}`); página da redação mostra correção quando corrigida.
- **Uploads**: validação por magic bytes (`upload_validator.py` — extensão vem dos bytes, nunca do nome do cliente); armazenamento via `StorageBackend` (`LocalStorage` hoje, R2 futuro); download protegido `GET /uploads/{caminho}` (404 para não autorizado; anônimo → login).

## Business rules

- Sessão por cookie assinado; todo POST exige `verificar_csrf` (token na sessão + campo oculto).
- Propriedade sempre validada (turma/aula pertence à professora logada; matrícula do aluno).
- Matrícula e conclusão idempotentes; concluir aula de turma não matriculada → erro.
- Redação: uma por matrícula+aula (UNIQUE); submissão exige matrícula e aula da turma da matrícula (anti-trapaça); correção única (redacao_id unique); notas C1–C5 validadas em 0–200 no service; antes da correção o reupload substitui texto e/ou arquivo; depois, nada.
- Uploads: PDF/JPG/PNG validados por magic bytes; ≤10MB; nome `uuid4().hex` + extensão detectada; download exige permissão (proposta: professor dono ou aluno matriculado; redação: aluno dono ou professor da turma) — negado responde 404, nunca 403.
- Query params vindos de select (ex.: filtro de turma) chegam como `str` — vazio é válido ("Todas as turmas" envia `?turma_id=`); nunca declarar `int` em query param opcional de filtro.
- Embed usa domínio canônico `https://www.youtube.com/embed/{id}?rel=0` (nocookie falhava com "Video unavailable").
- Flash: lista `[categoria, texto]` (success|error|info) — NÃO mudar para dict (base.html e testes dependem).

## Services

- `turma_service`: `criar_turma`, `editar_turma`, `excluir_turma`, `listar_turmas_por_professor`, `TIPOS_VALIDOS`.
- `aula_service`: `adicionar_aula`, `editar_aula`, `excluir_aula`, `reordenar_aulas`, `mover_aula`, getters (`buscar_turma_do_professor`, `buscar_aula_da_professora`, `listar_aulas_da_turma`).
- `matricula_service`: `matricular`, `listar_turmas_disponiveis`, `ja_matriculado`, `dados_dashboard`, `concluir_aula`, `listar_aulas_para_aluno` (itens com `tema` p/ botão de redação), `calcular_progresso`.
- `redacao_service`: `criar_proposta`, `listar_redacoes_pendentes`, `contar_redacoes_pendentes`, `obter_redacao_para_correcao`, `corrigir_redacao`, `submeter_redacao`, `listar_redacoes_do_aluno`, `obter_redacao_com_correcao`, `obter_dados_redacao_do_aluno`, `permitir_download_upload`, `COMPETENCIAS`/`NOTA_MIN`/`NOTA_MAX`.
- `upload_service`: `salvar_upload`, `substituir_upload` (validam via `upload_validator` e gravam via storage; storage injetável, default `get_storage()`).

## Tests

81 verdes: E2E (`test_auth`, `test_professor`, `test_aluno`, `test_progresso`, `test_redacao` — 16 do fluxo de redação, `test_upload` — 9 de upload/download) + unitários (`test_services`, `test_storage` — 7 do storage/factory/validador) + regressões de nav/select. Sempre TestClient + SQLite em /tmp (nunca no dev.db); uploads em diretório temporário (`UPLOADS_DIR` no conftest).

## Bugs corrigidos (lições)

1. CSRF inefetivo no FastAPI 0.141 (Response de dependência não interrompe endpoint) → exceção `RedirecionarComFlash` + handler global.
2. Flash #2 perdido (Session.modified só muda com `__setitem__`) → `flash()` força reatribuição.
3. Mover aulas violava UNIQUE → troca em 3 passos com sentinela `-1`.
4. Embed "Video unavailable" (youtube-nocookie) → domínio youtube.com.
5. Link "Turmas disponíveis" morto (nome de rota ≠ url_for) → renomear função; testes de nav adicionados.
6. Select "Tipo" vazio (refactor perdeu `tipos` no contexto) → passar `TIPOS_VALIDOS`.
7. `base.html` em recursão (tag `{% extends %}` dentro de comentário HTML — Jinja processa tags em comentários).
8. `raise RedirectResponse` em dependência → retorno/`RedirecionarComFlash`.
9. Filtro "Todas as turmas" gerava 422 (`?turma_id=` vazio não vira `int`) → rota aceita `str` e converte (vazio → None; não-dígito → flash de erro).

## Conventions

- Sempre `venv/bin/python` / `venv/bin/pip` (nunca python do sistema).
- **Nunca `git push`** — trabalho 100% local (commits ok). Remote origin existe, não usar.
- **Nunca excluir/resetar `dev.db` nem fazer backup** — banco dev é intocável; consultas read-only.
- Commits atômicos, mensagens em português com prefixo (`feat:`, `fix:`, `refactor:`, `chore:`).
- Routers finos (Form/flash/redirect), services com ValueError/RuntimeError, templates herdam `base.html` + Tailwind CDN.
- Nome de função da rota = nome usado em `url_for(...)` nos templates (senão link morre como `#`).
- Testes novos obrigatórios para qualquer mudança de rota/template (E2E) ou service (unit).
- Ruff: `venv/bin/ruff check .` e `venv/bin/ruff format .` antes de commit (config em `ruff.toml`; B008 Depends/Form e BLE001 services são exceções intencionais).

## Next (pós-Redação)

- Refinamentos RF08–10: limite de caracteres no textarea; comentário por competência (hoje só geral); gráfico de evolução das notas; destaque de trechos; limpeza de arquivos órfãos ao excluir aula.
- R2: implementar `R2Storage` (`app/storage/r2.py`, boto3 + URL assinada) e ativar via `STORAGE_BACKEND=r2`.
- Deploy: Dockerfile + Railway/Render + Postgres gerenciado.
- Financeiro (RF11-13), Analytics (RF14-15), Multi-professor (RF16), Extras (RF17-18) — ver Backlog futuro.

## Backlog futuro

- **Financeiro (RF11-13)**: planos, Mercado Pago/Stripe (PIX/boleto/cartão), controle de acesso pago.
- **Analytics (RF14-15)**: painel da turma (engajamento, distribuição de notas), relatório do aluno em PDF.
- **Multi-professor (RF16)**: cadastro de professores com isolamento (models já têm `professor_id`).
- **Extras (RF17-18)**: guias ENEM, metas do aluno, gamificação.

## Technical debt

- Deploy: Dockerfile + Railway/Render + Postgres gerenciado (`.env` com DATABASE_URL de produção).
- `R2Storage` (Cloudflare R2) pendente — `STORAGE_BACKEND=r2` levanta NotImplementedError; esqueleto documentado em `app/storage/r2.py`.
- PDF real via WeasyPrint em worker (HTML print já atende RF07).
- Tailwind: build próprio no lugar do CDN.
- Logs estruturados; páginas de erro customizadas (404/500) em vez de JSON do FastAPI.
- Warning de deprecation no TestClient: trocar `httpx` → `httpx2`.
- `SEED_PROFESSOR_SENHA` já suporta senha custom; e-mail do seed fixo (`carla@exemplo.com`).

## Notes

- (espaço para anotações rápidas futuras)
