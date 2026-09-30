"""Local token-protected REST service used by the MCP security exercise."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.getenv("REGISTRY_TOKEN", "workshop-local-token")
RECORD = {
    "registration_number": "J40/12345/2019",
    "legal_name": "Carpathia Localization SRL",
    "status": "active",
    "country": "Romania",
    "internal_note": "This field must never leave the registry boundary.",
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.headers.get("Authorization") != f"Bearer {TOKEN}":
            self.send_error(401)
            return
        if self.path != "/vendors/J40%2F12345%2F2019":
            self.send_error(404)
            return
        body = json.dumps(RECORD).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        print(format % args)  # Authorization headers and request bodies are intentionally omitted.


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Vendor registry listening on http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
