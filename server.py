#!/usr/bin/env python3
"""Servidor local para o app de finanças.

Serve os arquivos estáticos de ./public e expõe uma API para
autenticação (email/senha) e para ler/gravar os dados financeiros de
cada usuário no Firestore.
"""
import json
import os
import time
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import auth
import firestore_client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}

SESSION_COOKIE = "session"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    # ---------- helpers ----------

    def _send_json(self, obj, status=200, set_cookie=None, clear_cookie=False):
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if set_cookie:
            self.send_header("Set-Cookie", f"{SESSION_COOKIE}={set_cookie}; HttpOnly; Path=/; SameSite=Lax")
        if clear_cookie:
            self.send_header("Set-Cookie", f"{SESSION_COOKIE}=; HttpOnly; Path=/; SameSite=Lax; Max-Age=0")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        return json.loads(raw)

    def _current_email(self):
        raw_cookie = self.headers.get("Cookie")
        if not raw_cookie:
            return None
        jar = cookies.SimpleCookie()
        jar.load(raw_cookie)
        morsel = jar.get(SESSION_COOKIE)
        if not morsel:
            return None
        return auth.get_session_email(morsel.value)

    def _require_json_content_type(self):
        content_type = self.headers.get("Content-Type", "")
        return content_type.startswith("application/json")

    # ---------- GET ----------

    def do_GET(self):
        if self.path == "/api/data":
            email = self._current_email()
            if not email:
                self._send_json({"error": "Não autenticado"}, status=401)
                return
            data = firestore_client.get_user_data(email) or {"recurrences": [], "oneOffs": []}
            self._send_json({"recurrences": data.get("recurrences", []), "oneOffs": data.get("oneOffs", [])})
            return

        if self.path == "/api/me":
            email = self._current_email()
            if not email:
                self._send_json({"error": "Não autenticado"}, status=401)
                return
            self._send_json({"email": email})
            return

        path = self.path.split("?")[0]
        if path == "/":
            path = "/index.html"
        file_path = os.path.normpath(os.path.join(PUBLIC_DIR, path.lstrip("/")))
        if not file_path.startswith(PUBLIC_DIR) or not os.path.isfile(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return
        ext = os.path.splitext(file_path)[1]
        with open(file_path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", MIME_TYPES.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # ---------- POST ----------

    def do_POST(self):
        if self.path == "/api/register":
            self._handle_register()
            return
        if self.path == "/api/login":
            self._handle_login()
            return
        if self.path == "/api/logout":
            self._handle_logout()
            return
        if self.path == "/api/data":
            self._handle_save_data()
            return
        self.send_response(404)
        self.end_headers()

    def _handle_register(self):
        try:
            payload = self._read_json_body()
        except json.JSONDecodeError:
            self._send_json({"error": "JSON inválido"}, status=400)
            return

        email = auth.normalize_email(payload.get("email"))
        password = payload.get("password") or ""
        password_confirm = payload.get("password_confirm") or ""

        if not auth.is_valid_email(email):
            self._send_json({"error": "Email inválido"}, status=400)
            return
        if len(password) < 8:
            self._send_json({"error": "Senha deve ter ao menos 8 caracteres"}, status=400)
            return
        if password != password_confirm:
            self._send_json({"error": "As senhas não coincidem"}, status=400)
            return
        if firestore_client.get_user_auth(email):
            self._send_json({"error": "Email já cadastrado"}, status=409)
            return

        salt, password_hash = auth.hash_password(password)
        firestore_client.save_user_auth(email, {
            "email": email,
            "salt": salt,
            "password_hash": password_hash,
            "created_at": time.time(),
        })
        firestore_client.save_user_data(email, {"recurrences": [], "oneOffs": []})

        token = auth.create_session(email)
        self._send_json({"email": email}, set_cookie=token)

    def _handle_login(self):
        try:
            payload = self._read_json_body()
        except json.JSONDecodeError:
            self._send_json({"error": "JSON inválido"}, status=400)
            return

        email = auth.normalize_email(payload.get("email"))
        password = payload.get("password") or ""

        if auth.is_login_blocked(email):
            self._send_json({"error": "Muitas tentativas. Tente novamente em instantes."}, status=429)
            return

        user = firestore_client.get_user_auth(email)
        if not user or not auth.verify_password(password, user["salt"], user["password_hash"]):
            auth.register_login_failure(email)
            self._send_json({"error": "Email ou senha inválidos"}, status=401)
            return

        auth.register_login_success(email)
        token = auth.create_session(email)
        self._send_json({"email": email}, set_cookie=token)

    def _handle_logout(self):
        raw_cookie = self.headers.get("Cookie")
        if raw_cookie:
            jar = cookies.SimpleCookie()
            jar.load(raw_cookie)
            morsel = jar.get(SESSION_COOKIE)
            if morsel:
                auth.destroy_session(morsel.value)
        self._send_json({"ok": True}, clear_cookie=True)

    def _handle_save_data(self):
        email = self._current_email()
        if not email:
            self._send_json({"error": "Não autenticado"}, status=401)
            return
        if not self._require_json_content_type():
            self._send_json({"error": "Content-Type deve ser application/json"}, status=400)
            return
        try:
            payload = self._read_json_body()
        except json.JSONDecodeError:
            self._send_json({"error": "JSON inválido"}, status=400)
            return

        firestore_client.save_user_data(email, {
            "recurrences": payload.get("recurrences", []),
            "oneOffs": payload.get("oneOffs", []),
        })
        self._send_json({"ok": True})


def main():
    port = 8765
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Financas rodando em http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
