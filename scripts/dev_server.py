"""Tiny local server that exposes the Lambda handler on http://localhost:8787 for frontend development.
Usage: python scripts/dev_server.py   (reads .env from the repo root if present)"""
import base64, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
env = ROOT / ".env"
if env.exists():
    for line in env.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
from solarsabha.handlers.api import handler

class H(BaseHTTPRequestHandler):
    def _go(self, method):
        n = int(self.headers.get("content-length") or 0)
        ev = {"requestContext": {"http": {"method": method}}, "rawPath": self.path.split("?")[0],
              "headers": {k.lower(): v for k, v in self.headers.items()},
              "body": self.rfile.read(n).decode() if n else None}
        r = handler(ev)
        body = base64.b64decode(r["body"]) if r.get("isBase64Encoded") else r["body"].encode()
        self.send_response(r["statusCode"])
        for k, v in r["headers"].items():
            self.send_header(k, v)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        if r["statusCode"] != 204:
            self.wfile.write(body)
    def do_GET(self): self._go("GET")
    def do_POST(self): self._go("POST")
    def do_PUT(self): self._go("PUT")
    def do_DELETE(self): self._go("DELETE")
    def do_OPTIONS(self): self._go("OPTIONS")
    def log_message(self, *a): pass

print("API on http://localhost:8787")
ThreadingHTTPServer(("", 8787), H).serve_forever()
