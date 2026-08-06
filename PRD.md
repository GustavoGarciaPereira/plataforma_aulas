Aqui está um PRD detalhado para a plataforma, alinhado com tudo que você compartilhou até agora. Ele foi pensado para ser seu documento de referência durante o desenvolvimento, especialmente nas primeiras semanas de construção do piloto.

---

# 📄 PRD – Plataforma de Correção e Aulas de Redação

**Versão:** 1.0  
**Data:** 06/08/2026  
**Responsável:** [Seu nome]  
**Stack definida:** Python, FastAPI, Jinja2, PostgreSQL, Tailwind CSS

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

### 5.1 MVP (Semana 1) – Trilha de Aulas e Progresso

#### RF01 – Autenticação e Cadastro
- Cadastro de aluno: nome, e-mail, senha.
- Login para aluno e professor (sessão por cookies).
- Professor padrão criado via seed.

#### RF02 – Gestão de Turmas (Professor)
- Criar, editar e excluir turmas.
- Cada turma possui: nome, descrição, tipo (intensivo/regular).

#### RF03 – Criação e Ordenação de Aulas
- Adicionar aula à turma: título, URL do YouTube, ordem (número sequencial).
- O sistema deve converter automaticamente o link do YouTube em embed (iframe com controles).
- Reordenar aulas (arrastar ou seta para cima/baixo – opcional; MVP: apenas campo numérico).

#### RF04 – Matrícula do Aluno
- Aluno logado vê lista de turmas disponíveis.
- Clica em “Entrar na turma” → matrícula criada (sem validação financeira).
- Acesso à área da turma somente para alunos matriculados.

#### RF05 – Visualização das Aulas
- Página da turma exibe lista de aulas em ordem, cada uma com:
  - Título.
  - Player do YouTube incorporado.
  - Botão “Marcar como concluída”.
- A conclusão é registrada por matrícula e aula.

#### RF06 – Progresso do Aluno
- Dashboard pessoal com:
  - Turmas matriculadas.
  - Barra de progresso (percentual de aulas concluídas).
  - Últimas aulas assistidas.
- Na página da turma, indicador visual das aulas já concluídas.

#### RF07 – Cronograma para Download
- Rota que gera uma página HTML otimizada para impressão (ou PDF via WeasyPrint) com a lista de aulas (título, ordem) da turma.
- Botão “Baixar cronograma” na página da turma.

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
| Segurança | Senhas hash (bcrypt), sessões seguras, proteção CSRF nos formulários. Dados isolados por professor (no futuro). |
| Escalabilidade | Arquitetura monolítica simples, com possibilidade de adicionar workers assíncronos para tarefas pesadas (PDF, envio de e-mail). |
| Usabilidade | Interface responsiva (mobile-first), utilizando Tailwind CSS. Componentes autoexplicativos. |
| Manutenibilidade | Código estruturado em módulos (routers, models, templates). Migrações com Alembic. |
| Disponibilidade | Deploy em plataforma como Railway ou Render, com banco de dados gerenciado. |

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

- **Linguagem:** Python 3.11+
- **Framework web:** FastAPI (modo síncrono)
- **Templating:** Jinja2 (com herança de layouts)
- **ORM:** SQLAlchemy + psycopg2 (driver PostgreSQL síncrono)
- **Migrações:** Alembic
- **Banco de dados:** PostgreSQL 15+
- **Estilização:** Tailwind CSS via CDN (MVP), podendo evoluir para build próprio
- **Autenticação:** Sessões com cookies (Starlette SessionMiddleware) – simples e rápido
- **Geração de PDF:** WeasyPrint (para cronograma e futuros relatórios)
- **Deploy:** Docker + Railway / Render / VPS

**Estrutura de diretórios planejada:**

```
app/
  main.py
  database.py
  models.py
  routers/
    auth.py
    professor.py
    aluno.py
    turmas.py
    aulas.py
  templates/
    base.html
    ...
  static/
    (css, js, imagens se necessário)
alembic/
requirements.txt
Dockerfile
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
| Dificuldade de conversão do link do YouTube para embed | Implementar regex para extrair ID do vídeo e usar formato padrão de iframe. Testar com vários formatos de URL. |
| Baixa adoção dos alunos por falta de notificações | Como paliativo, o professor pode enviar link da plataforma via WhatsApp. Notificações automáticas entram no roadmap futuro. |
| Integração financeira complexa desacelera o MVP | Deixar pagamento por fora no início; a plataforma não terá bloqueio de acesso na V1. |
| Suporte a múltiplos professores exige alterações de arquitetura | Projetar models com `owner_id` e usar queries com filtro desde o início (mesmo com professor único), facilitando a transição. |

**Premissa:** O piloto será usado por uma única professora e um grupo controlado de alunos (≤ 30), sem necessidade de escalabilidade massiva.

---

## 12. Glossário

- **Trilha:** Conjunto ordenado de aulas dentro de uma turma.
- **Turma:** Agrupamento de alunos em um curso específico (ex: Intensivo ENEM).
- **Cronograma:** Lista sequencial das aulas com títulos e datas (no MVP, sem datas, apenas ordem).
- **Grade de competências:** Cinco critérios de correção (C1 a C5) normalmente alinhados ao ENEM.
- **Matrícula:** Vínculo entre aluno e turma, podendo ser gratuito (MVP) ou pago (versão posterior).

---


## 13. Apêndice – Prompt para Reasonix + DeepSeek (início do MVP)

Se você quiser iniciar o projeto agora com seu agente de codificação, pode utilizar o seguinte prompt:

> "Crie um projeto FastAPI com Jinja2 e PostgreSQL, estruturado em módulos. Utilize SQLAlchemy para ORM e Alembic para migrações. Implemente os seguintes modelos: Professor (id, nome, email, senha), Aluno (id, nome, email, senha), Turma (id, nome, descricao, professor_id FK), Aula (id, turma_id FK, titulo, youtube_url, ordem), Matricula (id, aluno_id FK, turma_id FK), AulaConcluida (id, matricula_id FK, aula_id FK, concluida_em). Configure sessões de autenticação com cookies. Gere telas com Tailwind CSS CDN. Inclua rotas de seed para criar um professor padrão. A aplicação deve permitir ao professor criar turma, adicionar aulas com URL do YouTube (convertida para embed automaticamente) e ordem; aluno se matricula, acessa turma, vê aulas em ordem com player do YouTube e botão 'Concluir'; dashboard do aluno mostra progresso; e rota para gerar cronograma em PDF (usando WeasyPrint)."

Assim você já tem a base do MVP. Depois é só iterar com prompts menores para cada funcionalidade adicional.

---

Com este PRD em mãos, você tem um norte claro para a semana de desenvolvimento intenso e para as fases seguintes. O documento pode ser revisado e complementado conforme novas ideias surgirem, mas mantenha o foco do piloto: **trilha de aulas, progresso e cronograma**. Boa sorte e mãos à obra!