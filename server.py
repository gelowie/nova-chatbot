from __future__ import annotations

import json
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from src.py import NovaEngine

# Configuration
HERE = Path(__file__).resolve().parent
BRAIN_PATH = HERE / "src" / "json" / "brain.json"
FRONTEND = HERE / "src" / "index.html"
HOST = "127.0.0.1"
PORT = 8000
MAX_BODY_BYTES = 64 * 1024

TEXT = "text/plain; charset=utf-8"
JSON = "application/json"

# Static file whitelist
STATIC_FILES = {
    "/docs/img/icon.png": (HERE / "docs" / "img" / "icon.png", "image/png"),
}

# Engine, built once at startup
engine = NovaEngine(BRAIN_PATH)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[nova] {self.address_string()} - {format % args}")

    # Response helpers
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str):
        body = json.dumps({"error": message}, separators=(",", ":")).encode()
        self._send(status, body, JSON)

    def _serve_file(self, path: Path, content_type: str, missing: bytes = b"not found"):
        if not path.exists():
            return self._send(404, missing, TEXT)
        self._send(200, path.read_bytes(), content_type)

    # Routes
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            return self._serve_file(
                FRONTEND, "text/html; charset=utf-8",
                missing=b"src/index.html is missing from this checkout.",
            )
        if path == "/health":
            return self._send(200, b'{"ok":true}', JSON)
        if path in STATIC_FILES:
            return self._serve_file(*STATIC_FILES[path])
        self._send(404, b"not found", TEXT)

    def do_POST(self):
        if self.path != "/chat":
            return self._send(404, b"not found", TEXT)

        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        # A negative length would make rfile.read() wait for EOF
        if length < 0:
            return self._error(400, "invalid content-length")
        if length > MAX_BODY_BYTES:
            return self._error(413, "request too large")
        raw = self.rfile.read(length) if length else b""

        try:
            payload = json.loads(raw or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._error(400, "invalid json")
        if not isinstance(payload, dict):
            return self._error(400, "body must be a JSON object")

        message = payload.get("message", "")
        if not isinstance(message, str):
            return self._error(400, "message must be a string")

        # Engine failures become a chat reply instead of a dropped connection
        try:
            reply = engine.respond(message)
        except Exception as err:
            traceback.print_exc()
            reply = {"text": f"⚠️ Internal error: {err}", "skill": "error", "suggestions": []}

        body = json.dumps(reply, ensure_ascii=False).encode("utf-8")
        self._send(200, body, "application/json; charset=utf-8")


# Entry point
def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"🟢 Nova engine listening on http://{HOST}:{PORT}")
    print(f"   Open http://{HOST}:{PORT} in your browser, or POST to /chat")
    print(f"   Brain loaded from: {BRAIN_PATH}")
    print(f"   Frontend file:     {FRONTEND}")
    print("   Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
