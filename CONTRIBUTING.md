# Contribuindo

Obrigado pelo interesse em contribuir com o **FinPilot**! Este documento
descreve como participar do projeto de forma organizada.

## Como contribuir

1. **Faça um fork** do repositório e clone localmente.
2. Crie uma branch para a sua mudança:

   ```bash
   git checkout -b feature/minha-melhoria
   ```

3. Faça os commits com mensagens claras e descritivas, em inglês ou português.
4. Envie a branch para o seu fork e abra um **Pull Request** para a `main`.

## Regras da main

A branch `main` é protegida:

- **Toda alteração entra via Pull Request** — nada de push direto.
- Cada PR precisa de **review e aprovação do code owner** (mantenedor).
- Reviews obsoletos são descartados quando o PR muda.

## O que faz um bom PR

- Escopo pequeno e focado (1 recurso ou correção por PR).
- Teste sua mudança localmente antes de abrir o PR.
- Descreva o que foi alterado e por quê no corpo do PR.
- Se a mudança for visual ou mudar comportamento, mencionar isso ajuda na revisão.

## Ambiente local

Consulte o `README.md` (seção *Executando localmente*) para configurar o
ambiente de desenvolvimento.

## Convenções de código

- Backend em Python puro (stdlib) — evite adicionar frameworks ao servidor.
- Frontend em HTML/CSS/JS vanilla, sem bibliotecas. Gráficos usam SVG.
- Mantenha compatibilidade com o modelo de dados existente do serviço de
  persistência ao adicionar novas funcionalidades.