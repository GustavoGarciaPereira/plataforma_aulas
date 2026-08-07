# ✍️ Plataforma de Redação

Plataforma web para uma professora de redação publicar **trilhas de aulas** (vídeos do YouTube), com **matrícula de alunos**, **controle de progresso** e **cronograma para download** — o MVP (Semana 1) do PRD está completo e testado.

> Documentos de referência: [PRD v1.1](PRD.md) (requisitos e decisões) · [AGENTS.md](AGENTS.md) (memória técnica do projeto)

---

## ✅ Funcionalidades (MVP — RF01 a RF07)

| | Funcionalidade |
|---|---|
| 🔐 | Cadastro de aluno, login de aluno/professora, logout (sessão por cookie + CSRF) |
| 🏫 | CRUD de turmas (nome, descrição, tipo) — só a professora dona |
| 🎬 | CRUD de aulas com URL do YouTube validada e **embed automático** (watch/youtu.be/embed/shorts/live), ordem automática e mover ↑↓ |
| 📝 | Matrícula do aluno em turmas disponíveis (idempotente) |
| ▶️ | Página da turma com player e botão **"Marcar como concluída"** (anti-trapaça, idempotente) |
| 📊 | Dashboard do aluno com barra de progresso e últimas aulas concluídas |
| 🖨️ | Cronograma da turma otimizado para impressão (Imprimir/Salvar PDF) |

## 🧱 Stack

Python 3.12 · FastAPI · Jinja2 · SQLAlchemy 2.0 · Alembic · PostgreSQL (produção) / SQLite (dev) · Tailwind CSS (CDN)

## 🚀 Como rodar

Pré-requisito: Python 3.12+.

```bash
cd ~/plataforma_aulas

# 1. Ambiente virtual
python3.12 -m venv venv
venv/bin/pip install -r requirements.txt        # runtime
venv/bin/pip install -r requirements-dev.txt    # testes

# 2. Configuração (.env na raiz — use .env.example como base)
cp .env.example .env
# Dev sem Postgres: DATABASE_URL=sqlite:///./dev.db (padrão já documentado)

# 3. Banco de dados
venv/bin/alembic upgrade head                   # cria as tabelas
venv/bin/python -m app.seed                     # professora padrão (idempotente)

# 4. Subir o servidor
venv/bin/uvicorn app.main:app --reload
```

Acesse **http://127.0.0.1:8000** — você será redirecionado para o login.

### Credenciais padrão

| Papel | E-mail | Senha |
|-------|--------|-------|
| Professora (Carla) | `carla@exemplo.com` | `123456` (ou `SEED_PROFESSOR_SENHA` na criação) |
| Aluno | cadastre pela tela "Criar conta" | — |

> ⚠️ Em produção: use PostgreSQL (altere `DATABASE_URL` no `.env`), gere um `SECRET_KEY` real (`python -c "import secrets; print(secrets.token_hex(32))"`) e defina `SEED_PROFESSOR_SENHA`.

## 🧪 Testes

```bash
venv/bin/python -m pytest tests/ -q    # 49 testes (E2E + unitários)
```

Os testes usam SQLite temporário em `/tmp` — **nunca** tocam no `dev.db` real.

## ✨ Lint e formatação (Ruff)

O projeto usa **Ruff** (linter + formatter em um binário, estilo Black). Config em `ruff.toml` (Python 3.12, linha de 100 caracteres; exceções documentadas: `Depends()`/`Form()` do FastAPI e `except Exception` nos services).

```bash
venv/bin/ruff check .        # lint — aponta erros e imports não usados
venv/bin/ruff format .       # formata o código automaticamente
venv/bin/ruff format --check .   # verifica se está tudo formatado (CI)
```

**Fluxo recomendado antes de cada commit:** `ruff check .` → `ruff format .` → `pytest tests/ -q`

Para corrigir erros de lint automaticamente: `venv/bin/ruff check . --fix`

## 📁 Estrutura

```
app/
  main.py            # aplicação + middlewares + rotas
  routers/           # auth, professor, aluno, utils (finos)
  services/          # turma_service, aula_service, matricula_service
  models.py          # Professor, Aluno, Turma, Aula, Matricula, AulaConcluida
  templates/         # 11 templates Jinja2 (Tailwind CDN)
  utils/             # youtube, csrf, flash, redirecionar
  config.py          # settings (.env)
alembic/             # migrações
tests/               # suíte E2E + unitários
PRD.md · AGENTS.md   # requisitos e memória do projeto
```

## 🗺️ Roadmap

- ✅ **Semana 1 (MVP):** RF01–RF07 — trilha de aulas, progresso, cronograma
- ⏳ **Semanas 2-3:** Redação — propostas, correção por competências (C1–C5), histórico (RF08–10)
- ⏳ **Semanas 4-5:** Financeiro — planos e pagamentos (RF11–13)
- ⏳ **Semanas 6-7:** Analytics — dashboards do professor (RF14–15)
- ⏳ **Semana 8+:** Múltiplos professores e extras (RF16–18)
- ⏳ **Deploy:** Dockerfile + Railway/Render + PostgreSQL
