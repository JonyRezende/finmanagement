# FinPilot — Finanças

Aplicação web de finanças pessoais: controle de fluxo de caixa mensal com
recorrências, parcelamentos, lançamentos avulsos, projeções e gráficos.

## Funcionalidades

- **Autenticação** por email/senha, com sessão via cookie (persistente no banco)
- **Extrato mensal** agrupado por dia, com saldo do mês anterior e saldo diário
- **Recorrências** com data de início/fim, parcelamento e ajustes pontuais por mês
- **Edição inteligente**: alterar apenas a ocorrência do mês ou a partir dela
- **Projeção** com tabela, gráfico de barras (entradas × saídas) e gráfico de
  linha do saldo projetado
- **Calculadora** incorporada

## Tecnologias

- **Backend**: Python (stdlib, HTTP server próprio) em camadas de domínio e
  serviços; persistência via Google Cloud Firestore
- **Frontend**: HTML/CSS/JS vanilla em módulos ESM, sem frameworks ou
  bundlers; gráficos em SVG
- **Testes**: pytest (unitários, de domínio e de API) + `node:test` para os
  módulos puros do frontend
- **CI/CD**: GitHub Actions — testes em push/PR e deploy automático na `main`
  via SSH + `systemd`

## Executando localmente

Requisitos: Python 3.11+ e credenciais de acesso ao Firestore (Application
Default Credentials, ex. via `GOOGLE_APPLICATION_CREDENTIALS` ou `gcloud auth
application-default login`).

```bash
# 1. Crie um ambiente virtual e instale as dependências
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Configure as credenciais de acesso aos dados
# 3. Suba o servidor
.venv/bin/python server.py
```

Abra no navegador o endereço local informado no terminal ao iniciar.

## Testes

```bash
# Backend (unitários, domínio e API)
.venv/bin/python -m pytest tests -q

# Frontend (módulos puros)
node --test tests/js/
```

## Estrutura do projeto

```
├── server.py                # ponto de entrada: inicia o servidor HTTP
├── src/financas/
│   ├── routes.py            # rotas HTTP e servidor
│   ├── app.py               # fachada ligando store, domínios e serviços
│   ├── errors.py            # erros com status HTTP
│   ├── config.py            # configuração (porta, caminhos, cookies)
│   ├── domains/             # lógica de negócio (auth, accounts, finance)
│   ├── services/            # serviços puros (password, sessions, rate_limit, rules)
│   └── infra/firestore.py   # persistência no Firestore
├── scripts/migrate_data.py  # utilitário de importação de dados legados
├── public/                  # frontend estático
│   ├── index.html           # painel de finanças
│   ├── login.html / account.html
│   ├── style.css / login.css
│   └── js/                  # módulos ESM (estado, projeção, extrato, gráficos, ...)
├── tests/                   # pytest (backend) e node:test (frontend)
└── requirements.txt
```

## Contribuindo

Veja o [CONTRIBUTING.md](CONTRIBUTING.md) para orientações sobre como
participar do projeto. Toda alteração na `main` passa por Pull Request.