#!/usr/bin/env python3
"""Servidor local para o app de finanças.

Serve os arquivos estáticos de ./public e expõe uma API simples para
ler/gravar o data.json (que guarda saldo, recorrências e lançamentos avulsos).
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
DATA_FILE = os.path.join(BASE_DIR, "data.json")

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/data":
            if not os.path.exists(DATA_FILE):
                self._send_json({"recurrences": [], "oneOffs": []})
                return
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self._send_json(json.load(f))
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

    def do_POST(self):
        if self.path == "/api/data":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                self._send_json({"error": "JSON invalido"}, status=400)
                return
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            self._send_json({"ok": True})
            return
        self.send_response(404)
        self.end_headers()


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
