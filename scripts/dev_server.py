"""Tiny local server that exposes the Lambda handler on http://localhost:8787 for frontend development.
Usage: python scripts/dev_server.py"""
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from solarsabha.handlers.api import handler

class H(BaseHTTPRequestHandler):
    def _go(self, method):
        n = int(self.headers.get("content-length") or 0)
        ev = {"requestContext": {"http": {"method": method}}, "rawPath": self.path.split("?")[0], "body": self.rfile.read(n).decode() if n else None}
        r = handler(ev)
        self.send_response(r["statusCode"]); [self.send_header(k, v) for k, v in r["headers"].items()]
        self.send_header("access-control-allow-headers", "*"); self.send_header("access-control-allow-methods", "*"); self.end_headers()
        self.wfile.write(r["body"].encode())
    do_GET = lambda s: s._go("GET"); do_POST = lambda s: s._go("POST"); do_OPTIONS = lambda s: s._go("OPTIONS")
    def log_message(self, *a): pass

print("API on http://localhost:8787"); HTTPServer(("", 8787), H).serve_forever()
