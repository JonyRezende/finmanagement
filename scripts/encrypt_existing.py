#!/usr/bin/env python3
"""Re-cifra dados financeiros legados (texto puro) com AES-GCM.

Uso:
    FINANCAS_ENCRYPTION_KEY="$(python3 -c 'import os,base64;print(base64.b64encode(os.urandom(32)).decode())')" python3 scripts/encrypt_existing.py

Usa a mesma configuração dos stores (FINANCAS_STORAGE, FINANCAS_SA_SECRET,
FINANCAS_ENCRYPTION_SECRET) e grava novamente, cifrado, cada user_data. Pode ser
rodado múltiplas vezes com segurança (dados já cifrados são pulados).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.financas.app import App, make_default_store  # noqa: E402


def main():
    app = App(store=make_default_store())
    emails = app.store.list_user_emails()
    if not emails:
        print("Nenhuma conta encontrada.")
        return
    for email in emails:
        doc = app.store.get_user_data(email)
        if doc and doc.get("v") == 2:
            print(f"Já cifrado: {email}")
            continue
        payload = app.finance.get_data(email)
        app.finance.save_data(email, payload)
        print(f"Re-cifrado: {email}")
    print("Concluído.")


if __name__ == "__main__":
    main()