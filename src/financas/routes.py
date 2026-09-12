"""Camada HTTP: serve os estáticos de ./public e expõe a API.

Roteamento fino; as regras de negócio vivem nos domínios (App).
"""
import json
import os
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import config
from .app import App
from .errors import Error
from .services import rules

UNAUTHENTICATED_MSG = "Não autenticado"

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; base-uri 'self'; "
        "frame-ancestors 'none'; form-action 'self'"
    ),
}


class FinancasServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, server_address, app):
        self.app = app
        super().__init__(server_address, Handler)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    # ---------- helpers ----------

    def _security_headers(self):
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)

    def _is_secure(self):
        return self.headers.get("X-Forwarded-Proto") == "https"

    def _send_json(self, obj, status=200, set_cookie=None, clear_cookie=False):
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        secure = "; Secure" if self._is_secure() else ""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if set_cookie:
            self.send_header("Set-Cookie", f"{config.SESSION_COOKIE}={set_cookie}; Max-Age=2592000; HttpOnly; Path=/; SameSite=Lax{secure}")
        if clear_cookie:
            self.send_header("Set-Cookie", f"{config.SESSION_COOKIE}=; HttpOnly; Path=/; SameSite=Lax{secure}; Max-Age=0")
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > config.MAX_BODY_BYTES:
            raise Error("Corpo da requisição muito grande", status=413)
        raw = self.rfile.read(length)
        return json.loads(raw)

    def _current_token(self):
        raw_cookie = self.headers.get("Cookie")
        if not raw_cookie:
            return None
        jar = cookies.SimpleCookie()
        jar.load(raw_cookie)
        morsel = jar.get(config.SESSION_COOKIE)
        return morsel.value if morsel else None

    def _current_email(self):
        token = self._current_token()
        return self.server.app.auth.email_for(token) if token else None

    def _respond_with_errors(self, handler_fn):
        try:
            handler_fn()
        except json.JSONDecodeError:
            self._send_json({"error": "JSON inválido"}, status=400)
        except Error as exc:
            self._send_json({"error": exc.message}, status=exc.status)

    # ---------- GET ----------

    def do_GET(self):
        if self.path == "/api/data":
            email = self._current_email()
            if not email:
                self._send_json({"error": UNAUTHENTICATED_MSG}, status=401)
                return
            self._send_json(self.server.app.finance.get_data(email))
            return

        if self.path == "/api/me":
            email = self._current_email()
            if not email:
                self._send_json({"error": UNAUTHENTICATED_MSG}, status=401)
                return
            self._send_json({"email": email})
            return

        path = self.path.split("?")[0]
        if path == "/":
            path = "/index.html"
        file_path = os.path.normpath(os.path.join(config.PUBLIC_DIR, path.lstrip("/")))
        if not file_path.startswith(config.PUBLIC_DIR) or not os.path.isfile(file_path):
            self.send_response(404)
            self._security_headers()
            self.end_headers()
            self.wfile.write(b"Not found")
            return
        ext = os.path.splitext(file_path)[1]
        with open(file_path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", config.MIME_TYPES.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    # ---------- POST ----------

    def _handle_register(self):
        def run():
            payload = self._read_json_body()
            email = rules.normalize_email(payload.get("email"))
            token = self.server.app.auth.register(
                email,
                payload.get("password") or "",
                payload.get("password_confirm") or "",
                ip=self.client_address[0],
            )
            self._send_json({"email": email}, set_cookie=token)
        self._respond_with_errors(run)

    def _handle_login(self):
        def run():
            payload = self._read_json_body()
            email = rules.normalize_email(payload.get("email"))
            token = self.server.app.auth.login(email, payload.get("password") or "", ip=self.client_address[0])
            self._send_json({"email": email}, set_cookie=token)
        self._respond_with_errors(run)

    def _handle_logout(self):
        token = self._current_token()
        if token:
            self.server.app.auth.logout(token)
        self._send_json({"ok": True}, clear_cookie=True)

    def _handle_change_password(self):
        def run():
            email = self._current_email()
            if not email:
                raise Error(UNAUTHENTICATED_MSG, status=401)
            payload = self._read_json_body()
            self.server.app.accounts.change_password(
                email,
                payload.get("current_password") or "",
                payload.get("new_password") or "",
                token=self._current_token(),
            )
            self._send_json({"ok": True})
        self._respond_with_errors(run)

    def _handle_change_email(self):
        def run():
            email = self._current_email()
            token = self._current_token()
            if not email:
                raise Error(UNAUTHENTICATED_MSG, status=401)
            payload = self._read_json_body()
            new_email = self.server.app.accounts.change_email(
                email,
                token,
                payload.get("current_password") or "",
                payload.get("new_email"),
            )
            self._send_json({"email": new_email})
        self._respond_with_errors(run)

    def _handle_save_data(self):
        def run():
            email = self._current_email()
            if not email:
                raise Error(UNAUTHENTICATED_MSG, status=401)
            if not self._require_json_content_type():
                raise Error("Content-Type deve ser application/json")
            payload = self._read_json_body()
            self.server.app.finance.save_data(email, payload)
            self._send_json({"ok": True})
        self._respond_with_errors(run)

    def _require_json_content_type(self):
        content_type = self.headers.get("Content-Type", "")
        return content_type.startswith("application/json")

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
        if self.path == "/api/account/password":
            self._handle_change_password()
            return
        if self.path == "/api/account/email":
            self._handle_change_email()
            return
        if self.path == "/api/data":
            self._handle_save_data()
            return
        self.send_response(404)
        self.end_headers()


def make_server(store=None, port=None):
    if port is None:
        port = config.PORT
    return FinancasServer(("127.0.0.1", port), App(store))


def main():
    server = make_server()
    print(f"Financas rodando em http://127.0.0.1:{config.PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass