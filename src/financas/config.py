"""Configurações centralizadas da aplicação."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}

SESSION_COOKIE = "session"
PORT = 8765
MAX_BODY_BYTES = 512_000

# Chave-mestra da criptografia dos dados financeiros em repouso.
# Produção: secret no Secret Manager (FINANCAS_ENCRYPTION_SECRET).
# Dev: variável FINANCAS_ENCRYPTION_KEY (base64 de 32 bytes).
ENCRYPTION_KEY_ENV = "FINANCAS_ENCRYPTION_KEY"
ENCRYPTION_SECRET_ENV = "FINANCAS_ENCRYPTION_SECRET"

# Backend de persistência: "auto" (Firestore se houver credenciais GCP, senão
# arquivo JSON local), "firestore" forçado ou "local" forçado.
STORAGE_BACKEND = os.environ.get("FINANCAS_STORAGE", "auto")
LOCAL_DB_PATH = os.environ.get("FINANCAS_DB", os.path.join(BASE_DIR, "financas-local.json"))