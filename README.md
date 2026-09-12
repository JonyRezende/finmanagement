# FinPilot — Finanças

Aplicação web de finanças pessoais: controle de fluxo de caixa mensal com
recorrências, parcelamentos, lançamentos avulsos, projeções e gráficos.

## Funcionalidades

- **Autenticação** por email/senha, com sessão via cookie
- **Extrato mensal** agrupado por dia, com saldo do mês anterior e saldo diário
- **Recorrências** com data de início/fim, parcelamento e ajustes pontuais por mês
- **Edição inteligente**: alterar apenas a ocorrência do mês ou a partir dela
- **Projeção** com tabela, gráfico de barras (entradas × saídas) e gráfico de
  linha do saldo projetado
- **Calculadora** incorporada

## Tecnologias

- **Backend**: Python (stdlib) com persistência gerenciada
- **Frontend**: HTML/CSS/JS sem dependências; gráficos em SVG

## Executando localmente

Requisitos: Python 3.11+ e acesso ao serviço de persistência de dados.

```bash
# 1. Crie um ambiente virtual e instale as dependências
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Configure as credenciais de acesso aos dados
# 3. Suba o servidor
.venv/bin/python server.py
```

Abra no navegador o endereço local informado no terminal ao iniciar.

## Estrutura do projeto

```
├── server.py               # servidor web e API
├── auth.py                 # autenticação e sessões
├── firestore_client.py     # acesso ao serviço de dados
├── migrate_existing_data.py# utilitário de importação de dados legados
├── requirements.txt
└── public/                 # frontend estático
    ├── index.html          # painel de finanças
    ├── app.js              # lógica do painel (extrato, projeção, gráficos)
    ├── login.html          # página de login/registro
    ├── login.js
    └── style.css / login.css
```

## Contribuindo

Veja o [CONTRIBUTING.md](CONTRIBUTING.md) para orientações sobre como
participar do projeto. Toda alteração na `main` passa por Pull Request.