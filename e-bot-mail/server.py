import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).parent.parent
FLAG_FILE = ROOT / "e-bot-mail" / "active"
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("BOT_PORT", 8001))


class BotHandler(BaseHTTPRequestHandler):

    def _send_json(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(payload))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/bot/status":
            self._send_json(200, {"active": FLAG_FILE.exists()})
        else:
            self._send_json(404, {"detail": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/bot/activate":
            params = parse_qs(parsed.query)
            token = params.get("token", [None])[0]
            if not BOT_TOKEN or token != BOT_TOKEN:
                self._send_json(403, {"detail": "Forbidden"})
                return
            FLAG_FILE.parent.mkdir(parents=True, exist_ok=True)
            FLAG_FILE.touch()
            self._send_json(200, {"status": "activated"})
        else:
            self._send_json(404, {"detail": "Not found"})

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), BotHandler)
    print(f"Bot server running on port {PORT}")
    server.serve_forever()
