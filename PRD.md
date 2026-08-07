Aqui está um PRD detalhado para a plataforma, alinhado com tudo que você compartilhou até agora. Ele foi pensado para ser seu documento de referência durante o desenvolvimento, especialmente nas primeiras semanas de construção do piloto.

---

# 📄 PRD – Plataforma de Correção e Aulas de Redação

**Versão:** 1.1  
**Data:** 06/08/2026  
**Responsável:** Gustavo Garcia Pereira  
**Status:** MVP Semana 1 (RF01–RF07) ✅ implementado e testado — 49 testes verdes  
**Stack definida:** Python 3.12, FastAPI, Jinja2, SQLAlchemy 2.0, Alembic, PostgreSQL (prod) / SQLite (dev), Tailwind CSS

> **Changelog:** v1.1 — decisões de implementação registradas na seção 14; v1.0 — documento original.

---

## 1. Resumo Executivo

A plataforma tem como objetivo digitalizar e escalar o trabalho de uma professora de redação, oferecendo uma experiência completa de ensino à distância. Na primeira fase (piloto de 1 semana), o foco é entregar uma trilha de cursos com vídeos do YouTube, controle de progresso e matrícula. As funcionalidades de correção de redação, grade de competências, gestão financeira e suporte a múltiplos professores serão adicionadas progressivamente, seguindo um roadmap de evolução contínua.

O produto será desenvolvido com tecnologias maduras e simples (FastAPI + Jinja server-side rendering), permitindo iteração rápida, e utilizará agentes de IA (Reasonix + DeepSeek) para acelerar a codificação.

---

## 2. Visão do Produto

**Para** uma professora de redação que deseja estruturar seus cursos online e acompanhar o desempenho dos alunos, **a plataforma** oferece um ambiente integrado de ensino, correção e acompanhamento, **diferente** de planilhas e ferramentas genéricas, **porque** centraliza desde a oferta das aulas até a correção detalhada por competências, fornecendo métricas de evolução e engajamento.

**Princípios**:
- Simplicidade de uso (UX enxuta, sem curva de aprendizado).
- Autonomia do professor para criar e gerir conteúdos.
- Foco na experiência do aluno (progresso visível, materiais acessíveis).

---

## 3. Objetivos do Produto

| Objetivo | Métrica (prazo) |
|----------|-----------------|
| Permitir que o professor publique trilhas de aulas e os alunos assistam dentro da plataforma | MVP (semana 1) |
| Oferecer visualização de progresso e download de cronograma | MVP (semana 1) |
| Receber redações e possibilitar correção estruturada (competências) | Semana 2-3 |
| Gerir pagamentos recorrentes e controlar acesso | Semana 4-5 |
| Suportar múltiplos professores, cada um com suas turmas | Semana 8+ |
| Fornecer dashboards analíticos para o professor | Semana 6-7 |

---

## 4. Personas

### 4.1 Professora (usuária administradora)
- **Nome:** Carla
- **Necessidades:**  
  - Criar turmas (ex: “Intensivo ENEM”, “Regular FUVEST”).  
  - Montar trilhas de aulas com vídeos e materiais complementares.  
  - Corrigir redações com grade de competências (C1 a C5).  
  - Acompanhar evolução de cada aluno e da turma.  
  - Exportar cronogramas e, futuramente, relatórios financeiros.  
- **Dores atuais:**  
  - Controle de entregas feito manualmente (e-mail, WhatsApp).  
  - Correção demorada e sem padronização.  
  - Dificuldade de mostrar progresso aos alunos.

### 4.2 Aluno
- **Nome:** João (16-22 anos, estudante pré-vestibular)
- **Necessidades:**  
  - Acessar aulas de forma organizada, sem sair do site.  
  - Entender seu progresso (o que já foi concluído, notas de redação).  
  - Baixar o cronograma para se planejar.  
  - Receber correção detalhada e visualizar evolução por competência.  
- **Dores atuais:**  
  - Perder prazos ou se sentir perdido sem um roadmap claro.  
  - Não enxergar melhoria ao longo do tempo.

---

## 5. Requisitos Funcionais

### 5.1 MVP (Semana 1) – Trilha de Aulas e Progresso — ✅ IMPLEMENTADO

#### RF01 – Autenticação e Cadastro ✅
- Cadastro de aluno: nome, e-mail, senha (hash bcrypt em `senha_hash` — nunca texto puro).
- Login para aluno e professor (sessão por cookies: `user_id`/`role`/`nome`); logout via **POST** (GET seria vulnerável a CSRF).
- Professor padrão criado via seed (`app/seed.py`, idempotente; senha sobrescrevível por `SEED_PROFESSOR_SENHA`).

#### RF02 – Gestão de Turmas (Professor) ✅
- Criar, editar e excluir turmas — somente a dona (validação de propriedade em todas as rotas).
- Cada turma possui: nome, descrição, tipo (intensivo/regular/outro — select com validação no servidor).

#### RF03 – Criação e Ordenação de Aulas ✅
- Aula: título, URL do YouTube, ordem (campo numérico; vazio = automática `MAX(ordem)+1`; duplicidade rejeitada).
- Conversão automática para embed: `https://www.youtube.com/embed/{id}?rel=0` (domínio canônico; o `youtube-nocookie.com` exibia “Video unavailable” em algumas redes).
- Bônus implementado: mover aula ↑/↓ (troca com a adjacente) e reordenação automática (1..n) após exclusões.

#### RF04 – Matrícula do Aluno ✅
- Aluno logado vê lista de turmas disponíveis (`/turmas-disponiveis`).
- “Entrar na turma” → matrícula criada (sem validação financeira) — **idempotente** (UNIQUE aluno+turma).
- Acesso à página da turma somente para matriculados (flash + redirect caso contrário).

#### RF05 – Visualização das Aulas ✅
- Página da turma (`/turmas/{id}`) exibe aulas em ordem, cada uma com player incorporado e botão “Marcar como concluída”.
- Conclusão registrada por matrícula+aula (`AulaConcluida`, UNIQUE) — idempotente e **anti-trapaça** (a aula precisa pertencer à turma da matrícula).
- Badge “✓ Concluída” + botão desabilitado após concluir.

#### RF06 – Progresso do Aluno ✅
- Dashboard pessoal: turmas matriculadas, barra de progresso (%), últimas aulas concluídas; botão “Ver aulas” no card.
- Indicador visual de conclusão na página da turma; navegação por papel (aluno x professora).

#### RF07 – Cronograma para Download ✅
- `/cronograma/{turma_id}` (exige login) → HTML otimizado para impressão (`@media print`, botão “Imprimir/Salvar PDF”).
- Botão “Baixar cronograma” na página da turma. PDF real via WeasyPrint: pós-MVP (worker assíncrono).

### 5.2 Semanas 2-3 – Submissão e Correção de Redação

#### RF08 – Proposta de Redação
- Professor pode anexar uma proposta a uma aula (tema, texto de apoio, comando).
- Campo de entrega para o aluno: editor de texto simples (textarea) com limite de caracteres ou upload de arquivo.

#### RF09 – Grade de Correção
- Interface de correção para o professor:
  - Visualizar redação do aluno.
  - Inserir nota para cada competência (C1 a C5, escala 0-200 ou 0-10).
  - Campo de comentário geral e campo específico por competência.
  - Destacar trechos e associar comentários (funcionalidade futura).

#### RF10 – Histórico e Devolutiva
- Aluno vê redações corrigidas com notas detalhadas e comentários.
- Dashboard do aluno expandido com gráfico de evolução das notas (linha do tempo).

### 5.3 Semanas 4-5 – Financeiro e Controle de Acesso

#### RF11 – Planos de Assinatura
- Professor configura planos (mensal, semestral, avulso) vinculados a turmas.
- Aluno no ato da matrícula escolhe o plano e é redirecionado para pagamento.

#### RF12 – Integração de Pagamento
- Integrar API de gateway (Mercado Pago, Stripe) para PIX, boleto e cartão.
- Status de pagamento: pendente, confirmado, expirado.
- Liberação de acesso à turma somente após confirmação do pagamento.

#### RF13 – Gestão Financeira (Professor)
- Listagem de alunos por turma, status de pagamento, data de vencimento.
- Renovação automática (se aplicável).
- Relatório de receita prevista e inadimplência.

### 5.4 Semanas 6-7 – Dashboards Analíticos (Professor)

#### RF14 – Painel da Turma
- Visão geral: total de alunos, média de conclusão das aulas, última atividade.
- Gráfico de engajamento (acessos diários).
- Distribuição de notas das redações.

#### RF15 – Relatório de Aluno
- Dados individuais: evolução por competência, redações entregues, frequência.
- Exportar em PDF.

### 5.5 Semana 8+ – Múltiplos Professores e Extras

#### RF16 – Cadastro de Novos Professores
- Interface de admin para criar contas de professor.
- Isolamento completo de dados (turmas, alunos, pagamentos) por professor.

#### RF17 – Guias do ENEM e Faculdade
- Páginas estáticas editáveis pelo professor (conteúdo rico) com dicas, critérios oficiais e exemplos.
- Acesso livre ou restrito a matriculados.

#### RF18 – Apresentação e Motivação
- Tela de boas-vindas do curso (vídeo de apresentação).
- Espaço “Metas do aluno” onde ele escreve seu objetivo (ex: “Alcançar 900+ no ENEM”).
- Selos e gamificação (ex.: “5 redações entregues”, “Evolução constante”).

---

## 6. Requisitos Não Funcionais

| Categoria | Especificação |
|-----------|---------------|
| Desempenho | Páginas renderizadas em < 200ms (server-side). Suporte a pelo menos 50 usuários simultâneos na V1. |
| Segurança | Senhas hash (bcrypt), sessões seguras, proteção CSRF nos formulários. Dados isolados por professor (no futuro). ✅ MVP: bcrypt (`app/security.py`), sessão por cookie assinado, CSRF com token de sessão + dependência `verificar_csrf` em todos os POSTs (login, cadastro, logout, CRUD, matrícula, conclusão). |
| Escalabilidade | Arquitetura monolítica simples, com possibilidade de adicionar workers assíncronos para tarefas pesadas (PDF, envio de e-mail). |
| Usabilidade | Interface responsiva (mobile-first), utilizando Tailwind CSS. Componentes autoexplicativos. |
| Manutenibilidade | Código estruturado em módulos (routers, models, templates). Migrações com Alembic. |
| Disponibilidade | Deploy em plataforma como Railway ou Render, com banco de dados gerenciado. ⏳ pendente (ver seção 14). |

---

## 7. Fluxos de Usuário Principais (MVP)

### 7.1 Professor cria turma e adiciona aulas
1. Login → Dashboard do professor.
2. Clica “Nova Turma” → preenche nome, descrição.
3. Acessa a turma → “Adicionar Aula”.
4. Insere título, cola link do YouTube, define ordem.
5. Repete para as demais aulas.
6. Na turma, pode baixar cronograma (gerado automaticamente).

### 7.2 Aluno ingressa, assiste e acompanha progresso
1. Cadastro/Login → Dashboard (vazio inicialmente).
2. Clica “Turmas disponíveis” → vê “Intensivo ENEM”.
3. Clica “Entrar na turma” → matrícula realizada.
4. Acessa a turma → lista de aulas.
5. Clica em uma aula → vídeo do YouTube aparece, ele assiste.
6. Ao terminar, clica “Concluir aula” → barra de progresso atualiza.
7. Clica em “Baixar cronograma” para obter PDF da lista de aulas.

---

## 8. Arquitetura e Stack Tecnológica

- **Linguagem:** Python 3.12 (venv do projeto: `plataforma_aulas/venv/`)
- **Framework web:** FastAPI 0.141 (modo síncrono)
- **Templating:** Jinja2 (herança de layouts; `app/templating.py` com context processors: usuário, flash, CSRF, `url_for` tolerante)
- **ORM:** SQLAlchemy 2.0 + psycopg2-binary (driver PostgreSQL síncrono)
- **Config:** pydantic-settings (`app/config.py` lê `.env` da raiz — DATABASE_URL, SECRET_KEY)
- **Migrações:** Alembic
- **Banco de dados:** PostgreSQL 15+ (produção) / **SQLite** (desenvolvimento local — `dev.db` na raiz, ignorado pelo git)
- **Estilização:** Tailwind CSS via CDN (MVP), podendo evoluir para build próprio
- **Autenticação:** Sessões com cookies assinados (Starlette SessionMiddleware + itsdangerous); CSRF com token de sessão
- **Geração de PDF:** ⏳ WeasyPrint pós-MVP (worker); MVP usa HTML com `@media print`
- **Deploy:** Docker + Railway / Render / VPS — ⏳ pendente

**Estrutura de diretórios atual:**

```
app/
  main.py            # app + middlewares + handler RedirecionarComFlash + routers
  config.py          # Settings (pydantic-settings, .env)
  database.py        # engine, SessionLocal, get_db
  models.py          # 6 models (SQLAlchemy 2.0, Mapped)
  dependencies.py    # get_current_user, require_professor
  security.py        # hash_senha / verificar_senha (bcrypt)
  seed.py            # professora Carla (idempotente)
  templating.py      # Jinja2Templates + context processors
  routers/
    auth.py          # /auth (RF01)
    professor.py     # /professor (RF02/RF03)
    aluno.py         # dashboard, turmas-disponiveis, turma, concluir (RF04/05/06)
    utils.py         # /cronograma (RF07)
  services/
    turma_service.py
    aula_service.py
    matricula_service.py
  utils/
    youtube.py       # extração de ID + embed
    csrf.py          # token + verificar_csrf
    flash.py         # flash() + processors
    redirecionar.py  # exceção RedirecionarComFlash
  templates/         # 11 templates (extends base.html, Tailwind CDN)
  static/
services  → app/services (acima)
tests/               # E2E (TestClient + SQLite temporário) e unitários de services
  conftest.py
  test_auth.py test_professor.py test_aluno.py test_progresso.py test_services.py
alembic/             # migração 1a2b3c4d5e6f (init)
requirements.txt
requirements-dev.txt
.env.example         # .env é local/ignorado
AGENTS.md            # memória do projeto (estado atual completo)
```

---

## 9. Roadmap e Cronograma

| Fase | Período | Entregáveis | Dependências |
|------|---------|-------------|--------------|
| **MVP** | Semana 1 | Autenticação, CRUD turmas/aulas, embed YouTube, matrícula, progresso, cronograma | Nenhuma |
| **Redação** | Semanas 2-3 | Submissão de redação, correção por competências, histórico aluno | MVP |
| **Financeiro** | Semanas 4-5 | Planos, checkout Mercado Pago, controle de acesso pago | MVP |
| **Analytics** | Semanas 6-7 | Dashboards professor, relatórios de turma e aluno | Redação |
| **Multi-professor** | Semana 8+ | Cadastro de múltiplos professores, isolamento de dados | MVP |
| **Guias e gamificação** | Contínuo | Páginas de conteúdo, selos, metas do aluno | MVP |

---

## 10. Métricas de Sucesso (MVP)

- **Professora consegue criar uma turma e 5 aulas em menos de 10 minutos.**
- **Aluno completa fluxo de cadastro → matrícula → assistir aula em menos de 3 minutos.**
- **Nenhuma falha crítica impede a reprodução dos vídeos incorporados.**
- **Cronograma gerado corretamente (lista fiel às aulas cadastradas).**
- **Feedback qualitativo da professora** positivo sobre a facilidade de uso.

---

## 11. Riscos e Premissas

| Risco | Mitigação |
|-------|-----------|
| Escopo se expandir durante o piloto (feature creep) | Congelar funcionalidades da semana 1; qualquer nova ideia vai para o backlog pós-MVP. |
| Dificuldade de conversão do link do YouTube para embed | ✅ Implementado em `app/utils/youtube.py` (regex testada: watch, youtu.be, embed, shorts, live, v; tolera URL sem protocolo). Embed usa o domínio canônico `youtube.com/embed` — o `youtube-nocookie.com` exibia “Video unavailable” em algumas redes/regiões. |
| Baixa adoção dos alunos por falta de notificações | Como paliativo, o professor pode enviar link da plataforma via WhatsApp. Notificações automáticas entram no roadmap futuro. |
| Integração financeira complexa desacelera o MVP | Deixar pagamento por fora no início; a plataforma não terá bloqueio de acesso na V1. |
| Suporte a múltiplos professores exige alterações de arquitetura | Projetar models com `owner_id` e usar queries com filtro desde o início (mesmo com professor único), facilitando a transição. |

**Premissa:** O piloto será usado por uma única professora e um grupo controlado de alunos (≤ 30), sem necessidade de escalabilidade massiva.

**Premissa v1.1:** Desenvolvimento local em SQLite (`dev.db`) — banco intocável (não excluir/resetar/backup); produção em PostgreSQL gerenciado.

---

## 12. Glossário

- **Trilha:** Conjunto ordenado de aulas dentro de uma turma.
- **Turma:** Agrupamento de alunos em um curso específico (ex: Intensivo ENEM).
- **Cronograma:** Lista sequencial das aulas com títulos e datas (no MVP, sem datas, apenas ordem).
- **Grade de competências:** Cinco critérios de correção (C1 a C5) normalmente alinhados ao ENEM.
- **Matrícula:** Vínculo entre aluno e turma, podendo ser gratuito (MVP) ou pago (versão posterior).

---


## 13. Apêndice – Prompt para Reasonix + DeepSeek (início do MVP)

> ✅ **Executado e evoluído.** O prompt abaixo foi a base do MVP; as decisões de implementação (constraints de unicidade, `senha_hash`, camada de services, CSRF, SQLite dev) estão na seção 14 e no `AGENTS.md`.

Se você quiser iniciar o projeto agora com seu agente de codificação, pode utilizar o seguinte prompt:

> "Crie um projeto FastAPI com Jinja2 e PostgreSQL, estruturado em módulos. Utilize SQLAlchemy para ORM e Alembic para migrações. Implemente os seguintes modelos: Professor (id, nome, email, senha), Aluno (id, nome, email, senha), Turma (id, nome, descricao, professor_id FK), Aula (id, turma_id FK, titulo, youtube_url, ordem), Matricula (id, aluno_id FK, turma_id FK), AulaConcluida (id, matricula_id FK, aula_id FK, concluida_em). Configure sessões de autenticação com cookies. Gere telas com Tailwind CSS CDN. Inclua rotas de seed para criar um professor padrão. A aplicação deve permitir ao professor criar turma, adicionar aulas com URL do YouTube (convertida para embed automaticamente) e ordem; aluno se matricula, acessa turma, vê aulas em ordem com player do YouTube e botão 'Concluir'; dashboard do aluno mostra progresso; e rota para gerar cronograma em PDF (usando WeasyPrint)."

Assim você já tem a base do MVP. Depois é só iterar com prompts menores para cada funcionalidade adicional.

---

Com este PRD em mãos, você tem um norte claro para a semana de desenvolvimento intenso e para as fases seguintes. O documento pode ser revisado e complementado conforme novas ideias surgirem, mas mantenha o foco do piloto: **trilha de aulas, progresso e cronograma**. Boa sorte e mãos à obra!

---

## 14. Changelog v1.1 — Decisões de Implementação (MVP concluído)

Diferenças entre o PRD original (v1.0) e o que foi realmente implementado no MVP da Semana 1:

| # | Decisão | Detalhe |
|---|---------|---------|
| 1 | `senha` → `senha_hash` | Nunca armazenar senha em texto puro; bcrypt via `app/security.py`; seed com `SEED_PROFESSOR_SENHA` |
| 2 | UniqueConstraints adicionais | `UNIQUE(turma_id, ordem)` (ordem duplicada), `UNIQUE(aluno_id, turma_id)` (matrícula duplicada), `UNIQUE(matricula_id, aula_id)` (conclusão duplicada) |
| 3 | `Turma.tipo` ganhou “outro” | Select validado no servidor (`TIPOS_VALIDOS` no service) |
| 4 | Logout via POST | GET/logout seria vulnerável a CSRF; todos os POSTs têm `verificar_csrf` |
| 5 | CSRF com token de sessão | Campo oculto nos forms + dependência; FastAPI 0.141 não interrompe endpoint com Response de dependência → exceção `RedirecionarComFlash` + handler global |
| 6 | Camada de services | `app/services/` (turma/aula/matricula) com ValueError (flash amigável) e RuntimeError (rollback + flash genérico); routers finos |
| 7 | Embed usa `youtube.com/embed` | `youtube-nocookie.com` exibia “Video unavailable” em algumas redes (bug real corrigido) |
| 8 | Cronograma: HTML `@media print` | WeasyPrint adiado para worker (PRD permite HTML otimizado para impressão) |
| 9 | Banco dev = SQLite (`dev.db`) | Produção segue PostgreSQL 15+; `.env.example` documenta as duas opções |
| 10 | Ordem de aulas | Auto `MAX(ordem)+1` + rejeição de duplicidade + mover ↑/↓ (bônus) + reordenação pós-exclusão |
| 11 | Conclusão anti-trapaça | Aula precisa pertencer à turma da matrícula; matrícula resolvida pela turma da aula + aluno da sessão |
| 12 | Dependências extras | `itsdangerous` (SessionMiddleware), `python-multipart` (Form), `pydantic-settings`, `httpx`/`pytest` (dev) |

**Status do MVP:** RF01–RF07 ✅ · 49 testes verdes · fluxo completo do aluno validado (10/10 passos) · 7+ commits locais (sem push).

**Próximos passos:** Semanas 2-3 (RF08–RF10 — redação e correção C1–C5, detalhado no AGENTS.md) → deploy (Dockerfile + Railway/Render + Postgres) → Financeiro (RF11–13) → Analytics (RF14–15) → Multi-professor (RF16) → Extras (RF17–18).