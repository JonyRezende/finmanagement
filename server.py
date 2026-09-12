#!/usr/bin/env python3
"""Entry point compatível: delega para o pacote em src/financas.

Mantém o mesmo caminho usado pelo systemd (python server.py).
"""
from src.financas.routes import main

if __name__ == "__main__":
    main()