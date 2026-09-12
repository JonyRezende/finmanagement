# FinPilot — Finanças

Aplicação web de finanças pessoais. Serve para controlar o fluxo de caixa
mensal: você cadastra suas receitas e despesas (fixas, parceladas ou avulsas) e
o sistema monta o extrato do mês, projeta os próximos meses e mostra os
impactos no saldo por meio de tabelas e gráficos.

## Funcionalidades

- **Autenticação** por email/senha, com sessão via cookie (persistente no banco)
- **Extrato mensal** agrupado por dia, com saldo do mês anterior e saldo diário
- **Recorrências** com data de início/fim, parcelamento e ajustes pontuais por mês
- **Edição inteligente**: alterar apenas a ocorrência do mês ou a partir dela
- **Projeção** (7 meses) com tabela, gráfico de barras (entradas × saídas) e
  gráfico de linha do saldo projetado
- **Calculadora** incorporada
- **Gerenciamento de conta**: trocar senha e email (migra dados/sessões)

## Stack

| Camada        | Tecnologias |
|---------------|-------------|
| Backend       | Python (stdlib) — servidor HTTP próprio (`http.server.ThreadingHTTPServer`), zero frameworks |
| Persistência  | Google Cloud Firestore |
| Frontend      | HTML/CSS/JS vanilla, módulos ESM, sem frameworks ou bundlers; gráficos em SVG |
| Testes        | pytest (backend) + `node:test` (frontend) |
| Lint          | ruff |
| Qualidade     | SonarCloud (análise estática + quality gate) |
| CI/CD         | GitHub Actions |
| Deploy        | VPS Linux com `systemd`; HTTPS via Let's Encrypt + Cloudflare |

## Arquitetura

```
                    ┌──────────────────────────────────────────┐
                    │        Frontend (public/)                │
                    │  HTML/CSS + Módulos ESM (js/)            │
                    │   - puros: calendar, money,              │
                    │     projections, calculator              │
                    │   - DOM:  state, api, charts,            │
                    │     projection, extrato, txnForm, main   │
                    └──────────────────┬───────────────────────┘
                                       │ fetch JSON (cookie de sessão)
                    ┌──────────────────▼───────────────────────┐
   HTTP/ESTÁTICO    │  routes.py: FinancasServer + Handler     │
  ──► + /api/* JSON │  (serve public/ e delega regras)         │
                    └──────────────────┬───────────────────────┘
                                       │ App (app.py) — fachada
                    ┌──────────────────▼───────────────────────┐
                    │  Domains (regra de negócio)              │
                    │   auth     – register/login/logout       │
                    │   accounts – senha/email                 │
                    │   finance  – dados financeiros           │
                    └──────────────────┬───────────────────────┘
                                       │ Store (interface injetável)
                    ┌──────────────────▼───────────────────────┐
                    │  Services (lógica pura, testável)        │
                    │   password  – hash PBKDF2                │
                    │   sessions  – tokens com TTL + cache     │
                    │   rate_limit– 5 tentativas/60s por email │
                    │   rules     – validações                 │
                    └──────────────────┬───────────────────────┘
                                       │
                    ┌──────────────────▼───────────────────────┐
                    │  infra/firestore.py: FirestoreStore      │
                    │   users/{email} · user_data/{email}      │
                    │   sessions/{token}                       │
                    └──────────────────────────────────────────┘
```

Princípios:

- **Roteamento fino**: `routes.py` só lida com HTTP — toda regra de negócio
  vive nos domínios.
- **Injeção de dependência**: os domínios dependem de uma interface `Store`.
  Em produção o `App` injeta o `FirestoreStore`; nos testes um `FakeStore` em
  memória com as mesmas assinaturas — API e domínios rodam offline.
- **Serviços puros**: `password`, `sessions`, `rate_limit` e `rules` não têm
  dependência de HTTP/Firestore, o que os torna diretamente testáveis.
- **Frontend modular**: a lógica de projeção/calendário/dinheiro é separada do
  DOM em módulos puros, também testáveis em `node:test`.

## API

`POST /api/register` · `POST /api/login` · `POST /api/logout` ·
`POST /api/account/password` · `POST /api/account/email` ·
`GET/POST /api/data` · `GET /api/me`

Autenticação por cookie `session` (HttpOnly, 30 dias). Dados financeiros:
`{"recurrences": [...], "oneOffs": [...]}`.

## Qualidade

- **Lint**: `ruff` (config em `pyproject.toml`) roda em todo push/PR.
- **Testes backend**: 42 testes — unitários dos serviços, domínios e API
  completa (servidor real em porta efêmera + `FakeStore`).
- **Testes frontend**: `node:test` nos módulos puros (29 testes: projeção,
  recorrências, moeda, calendário e calculadora).
- **Cobertura**: `pytest-cov` gera `coverage.xml` e alimenta o SonarCloud.
- **SonarCloud**: análise estática com quality gate; o status é reportado como
  check nos Pull Requests.

Tudo isso roda no workflow **Tests** do GitHub Actions (lint, unit, js,
sonarcloud) em pushes na `main` e em PRs — e manualmente pela aba Actions.

## Executando localmente

Requisitos: Python 3.11+ e credenciais de acesso ao Firestore (Application
Default Credentials — ex. via `GOOGLE_APPLICATION_CREDENTIALS` apontando para
uma service account, ou `gcloud auth application-default login`).

```bash
# 1. Crie um ambiente virtual e instale as dependências
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Configure as credenciais de acesso aos dados
# 3. Suba o servidor
.venv/bin/python server.py
```

Abra no navegador o endereço local informado no terminal ao iniciar
(`http://127.0.0.1:8765`).

## Testes e lint (local)

```bash
.venv/bin/pip install -r requirements-dev.txt

# Backend (unitários, domínio e API) + cobertura
.venv/bin/python -m pytest tests --cov=src --cov-report=xml -q

# Frontend (módulos puros)
node --test tests/js/

# Lint
.venv/bin/ruff check .
```

## Deploy

Automatizado pelo GitHub Actions:

1. Todo **push/merge na `main`** roda o workflow **Tests**.
2. Com os checks verdes, o workflow **Deploy** entra em ação por SSH: faz
   `git pull` no servidor e reinicia o serviço via `systemd`, seguido de um
   smoke test no site.
3. Também é possível disparar manualmente pela aba Actions.

A `main` é protegida: mudanças entram via Pull Request.

## Estrutura do projeto

```
├── server.py                # ponto de entrada: inicia o servidor HTTP
├── src/financas/
│   ├── routes.py            # camada HTTP (estáticos + API)
│   ├── app.py               # fachada ligando store, domínios e serviços
│   ├── errors.py            # erros com status HTTP
│   ├── config.py            # configuração (porta, caminhos, cookies)
│   ├── domains/             # regras de negócio (auth, accounts, finance)
│   ├── services/            # lógica pura (password, sessions, rate_limit, rules)
│   └── infra/firestore.py   # persistência (FirestoreStore)
├── scripts/migrate_data.py  # utilitário de importação de dados legados
├── public/                  # frontend estático
│   ├── index.html           # painel de finanças
│   ├── login.html / account.html
│   ├── style.css / login.css
│   └── js/                  # módulos ESM (estado, projeção, extrato, gráficos, ...)
├── tests/                   # pytest (backend) + node:test (frontend)
├── pyproject.toml           # configuração do ruff
├── sonar-project.properties # configuração do SonarCloud
└── requirements.txt
```

## Contribuindo

Veja o [CONTRIBUTING.md](CONTRIBUTING.md) para orientações sobre como
participar do projeto. Toda alteração na `main` passa por Pull Request.