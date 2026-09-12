# FinPilot — Finanças

Aplicação web de finanças pessoais: controle de fluxo de caixa mensal com
recorrências, parcelamentos, lançamentos avulsos, projeções e gráficos.

## Funcionalidades

- **Autenticação** por email/senha (hash PBKDF2 em Firestore, sessão via cookie)
- **Extrato mensal** agrupado por dia, com saldo do mês anterior e saldo diário
- **Recorrências** com data de início/fim, parcelamento e ajustes pontuais por mês
- **Edição inteligente**: alterar apenas a ocorrência do mês ou a partir dela
- **Projeção de 6 meses** com tabela, gráfico de barras (entradas × saídas) e
  gráfico de linha do saldo projetado
- **Calculadora** lateral
- Dados armazenados por usuário no **Cloud Firestore**

## Tecnologias

- **Backend**: Python 3.11+ (stdlib `http.server`) + Cloud Firestore
- **Frontend**: HTML/CSS/JS vanilla (sem dependências), gráficos via SVG
- **Infra**: nginx (reverse proxy + TLS via Let's Encrypt), Google Cloud

## Executando localmente

Requisitos: Python 3.11+, credenciais do Google Cloud com acesso ao Firestore.

```bash
# 1. Crie um ambiente virtual e instale as dependências
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Aponte as credenciais do Google Cloud (Application Default Credentials)
export GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credentials.json

# 3. Suba o servidor
.venv/bin/python server.py
```

Acesse em <http://127.0.0.1:8765>.

## Estrutura do projeto

```
├── server.py               # servidor HTTP e API (/api/{register,login,logout})
├── auth.py                 # hashing de senha, sessões, rate limit
├── firestore_client.py     # acesso ao Firestore (users, user_data)
├── migrate_existing_data.py# migra data.json para uma conta no Firestore
├── requirements.txt
└── public/                 # frontend estático
    ├── index.html          # painel de finanças
    ├── app.js              # lógica do painel (extrato, projeção, gráficos)
    ├── login.html          # página de login/registro
    ├── login.js
    └── style.css / login.css
```

## Modelo de dados (Firestore)

- `users/{email}` — credenciais (`salt`, `password_hash`, `created_at`)
- `user_data/{email}` — dados financeiros (`recurrences`, `oneOffs`)

## Migração de dados existentes

Para importar um `data.json` legado para uma conta nova:

```bash
.venv/bin/python migrate_existing_data.py "seu-email@exemplo.com" "sua-senha"
```

## Deploy

A aplicação roda atrás do nginx, que faz proxy para `127.0.0.1:8765` e termina
TLS com certificado Let's Encrypt (renovação automática via systemd timer).
O serviço é gerenciado pelo systemd.

```bash
sudo systemctl restart financas   # reinicia o app
sudo systemctl status financas    # acompanha o status
```