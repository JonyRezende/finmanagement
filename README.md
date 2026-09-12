# FinPilot — Finanças pessoais

Aplicação web de finanças pessoais para controle de fluxo de caixa mensal:
recorrências, parcelamentos, lançamentos avulsos, projeção de saldo e gráficos.
Autenticação por email/senha e dados persistidos no Google Cloud Firestore.

## Funcionalidades

- **Autenticação** por email/senha, com sessão via cookie persistente no banco
  e rate limiting contra força bruta
- **Extrato mensal** agrupado por dia, com saldo do mês anterior e saldo diário
- **Recorrências** com data de início/fim, parcelamento e ajustes pontuais por mês
- **Edição inteligente**: alterar apenas a ocorrência do mês ou a partir dela
- **Projeção** com tabela, gráfico de barras (entradas × saídas) e gráfico de
  linha do saldo projetado
- **Calculadora** incorporada

## Tecnologias

- **Backend**: Python (stdlib, HTTP server próprio), organizado em camadas de
  domínio e serviços
- **Persistência**: Google Cloud Firestore; credencial da service account via
  Secret Manager
- **Frontend**: HTML/CSS/JS vanilla em módulos ESM, sem frameworks nem
  bundlers; gráficos em SVG
- **Testes**: pytest (unitários, de domínio e de API) + `node:test` para os
  módulos puros do frontend
- **CI/CD**: GitHub Actions — testes e análise do SonarCloud em push/PR e
  deploy automático na `main` via SSH + `systemd`

## Testes e qualidade

![Quality Gate](https://sonarcloud.io/api/project_badges/quality_gate?project=JonyRezende_finmanagement)
![Coverage](https://sonarcloud.io/api/project_badges/measure?project=JonyRezende_finmanagement&metric=coverage)
![Reliability](https://sonarcloud.io/api/project_badges/measure?project=JonyRezende_finmanagement&metric=reliability_rating)
![Security](https://sonarcloud.io/api/project_badges/measure?project=JonyRezende_finmanagement&metric=security_rating)
![Maintainability](https://sonarcloud.io/api/project_badges/measure?project=JonyRezende_finmanagement&metric=sqale_rating)

```bash
# Backend (unitários, domínio e API)
.venv/bin/python -m pytest tests -q

# Frontend (módulos puros)
node --test tests/js/
```

## Como executar localmente

Requisitos: **Python 3.11+** e acesso ao Google Cloud (Application Default
Credentials — ex. `gcloud auth application-default login` — ou
`GOOGLE_APPLICATION_CREDENTIALS`).

```bash
# 1. Crie um ambiente virtual e instale as dependências
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Configure as credenciais de acesso aos dados
# 3. Suba o servidor
.venv/bin/python server.py
```

Abra no navegador o endereço local informado no terminal ao iniciar.

## Estrutura e arquitetura

Arquitetura simplificada: o **frontend** (ESM vanilla) fala com um servidor
HTTP em Python stdlib; as **rotas** delegam para **domínios** (regras de
negócio) e **serviços** (lógica pura — senha, sessões, validação); a
**persistência** fica no Firestore via uma Store injetada, com a credencial
carregada do Secret Manager.

```
├── server.py                # ponto de entrada: inicia o servidor HTTP
├── src/financas/
│   ├── routes.py            # rotas HTTP e servidor
│   ├── app.py               # fachada ligando store, domínios e serviços
│   ├── errors.py            # erros com status HTTP
│   ├── config.py            # configuração (porta, caminhos, cookies)
│   ├── domains/             # lógica de negócio (auth, accounts, finance)
│   ├── services/            # serviços puros (password, sessions, rate_limit, rules)
│   └── infra/firestore.py   # persistência no Firestore (Secret Manager)
├── scripts/migrate_data.py       # utilitário de importação de dados legados
│   └── provision_credential.sh   # provisiona a credencial da SA no Secret Manager
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