---
name: quality-gate
description: 'Portão de qualidade: ruff check/format + pytest antes de commit (sem push, dev.db intocável)'
---

# Skill: quality-gate — portão de qualidade do projeto (plataforma_aulas)

Executa o fluxo de qualidade completo do projeto antes de fechar um trabalho e oferece o commit. Roda em loop no contexto do agente principal (inline).

## Fluxo

1. **Lint**: `venv/bin/ruff check .` (config em `ruff.toml`).
   - Erros auto-corrigíveis → `venv/bin/ruff check . --fix`.
   - Erros manuais → corrigir no arquivo (linhas longas, imports, variáveis mortas, `datetime` com timezone).
   - NÃO silenciar regras novas no `ruff.toml` sem justificativa forte — B008 (Depends/Form do FastAPI) e BLE001 (`except Exception` nos services) já estão configurados como exceções intencionais.

2. **Formatação**: `venv/bin/ruff format .` e confirmar com `venv/bin/ruff format --check .`.

3. **Testes**: `venv/bin/python -m pytest tests/ -q` (49+ testes: E2E TestClient + unitários).
   - Diagnosticar cada falha (traceback completo), distinguir bug de produção × bug de teste × problema ambiental.
   - Corrigir e re-rodar; no máximo 2 tentativas na mesma falha — se persistir, PARAR e explicar.
   - Se a falha for ambiental (dependência ausente, toolchain), parar e avisar em vez de instalar por conta própria.

4. **Commit** (se tudo verde): `git add -A` + mensagem em português com prefixo (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:`), atômico (um assunto por commit). SEMPRE `git commit` local — **nunca `git push`**.

## Regras inegociáveis

- Sempre `venv/bin/python` / `venv/bin/pip` / `venv/bin/ruff` — nunca o Python do sistema.
- **Nunca excluir, resetar ou fazer backup do `dev.db`** — banco dev é intocável; testes usam SQLite temporário em `/tmp` (conftest.py).
- Não alterar o `dev.db` com dados de teste; consultas read-only no banco real.
- Não pular/suprimir testes para forçar verde — corrigir a causa.
- Não fazer push em hipótese alguma (remote origin existe, não usar).

## Saída esperada

Resumo curto: `ruff check` (n erros → 0), `ruff format` (n arquivos), `pytest` (n passed) e o hash do commit criado.
