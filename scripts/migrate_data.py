#!/usr/bin/env python3
"""Migra o data.json atual para uma conta nova no Firestore.

Uso:
    python3 scripts/migrate_data.py seu-email@example.com "sua-senha-nova"

Cria a conta (mesmo fluxo do /api/register) e grava o conteúdo atual de
data.json como os dados financeiros dessa conta. Rode uma única vez.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.financas.domains import auth  # noqa: E402
from src.financas.infra import firestore  # noqa: E402

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(PROJECT_ROOT, "data.json")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    email = auth.normalize_email(sys.argv[1])
    password = sys.argv[2]

    if not auth.is_valid_email(email):
        print("Email inválido.")
        sys.exit(1)
    if len(password) < 8:
        print("Senha deve ter ao menos 8 caracteres.")
        sys.exit(1)
    if firestore.get_user_auth(email):
        print(f"Já existe uma conta para {email}. Abortando.")
        sys.exit(1)
    if not os.path.exists(DATA_FILE):
        print(f"Arquivo {DATA_FILE} não encontrado.")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        existing_data = json.load(f)

    salt, password_hash = auth.hash_password(password)
    firestore.save_user_auth(email, {
        "email": email,
        "salt": salt,
        "password_hash": password_hash,
        "created_at": time.time(),
    })
    firestore.save_user_data(email, {
        "recurrences": existing_data.get("recurrences", []),
        "oneOffs": existing_data.get("oneOffs", []),
    })

    print(f"Conta criada e dados migrados para {email}.")


if __name__ == "__main__":
    main()