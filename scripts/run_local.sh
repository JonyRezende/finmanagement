#!/usr/bin/env bash
# Executa a aplicação localmente com criptografia configurada.
#
# Gera (uma única vez) e persiste a chave-mestra em .financas-key, cifa dados
# legados do financas-local.json e inicia o servidor com FINANCAS_STORAGE=local.
#
# Uso:
#     ./scripts/run_local.sh
#
# Se FINANCAS_ENCRYPTION_KEY já estiver exportada, ela é respeitada.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEY_FILE="$PROJECT_ROOT/.financas-key"

if [[ -z "${FINANCAS_ENCRYPTION_KEY:-}" ]]; then
    if [[ ! -f "$KEY_FILE" ]]; then
        echo "Gerando nova chave de criptografia em .financas-key"
        python3 -c 'import os,base64;print(base64.b64encode(os.urandom(32)).decode())' > "$KEY_FILE"
        chmod 600 "$KEY_FILE"
    fi
    export FINANCAS_ENCRYPTION_KEY="$(cat "$KEY_FILE")"
fi

echo "Re-cifrando dados legados do JSON local (se houver)..."
FINANCAS_STORAGE=local "$PROJECT_ROOT/.venv/bin/python" "$PROJECT_ROOT/scripts/encrypt_existing.py"

echo "Iniciando servidor em http://127.0.0.1:8765"
exec env FINANCAS_STORAGE=local FINANCAS_ENCRYPTION_KEY="$FINANCAS_ENCRYPTION_KEY" \
    "$PROJECT_ROOT/.venv/bin/python" "$PROJECT_ROOT/server.py"