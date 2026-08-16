import imaplib
import email as email_lib
import re
import json
import os
import time
import threading
import requests
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).parent.parent
FLAG_FILE = ROOT / "e-bot-mail" / "active"
LOG_DIR = ROOT / "e-bot-mail" / "logs"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("BOT_PORT", 8001))
IMAP_SERVER = os.environ.get("EMAIL_IMAP_SERVER", "webreus.email")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

TRIGGER_SENDER = "noreply@deimmowinkel.be"
TRIGGER_SUBJECT = "Nieuwe keuringsaanvraag"
POLL_INTERVAL = 30


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._current_href = None
        self._current_text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs_dict = dict(attrs)
            self._current_href = attrs_dict.get('href')
            self._current_text = []

    def handle_data(self, data):
        if self._current_href is not None:
            self._current_text.append(data.strip())

    def handle_endtag(self, tag):
        if tag == 'a' and self._current_href:
            text = ' '.join(t for t in self._current_text if t)
            self.links.append({'text': text, 'url': self._current_href})
            self._current_href = None
            self._current_text = []


def extract_links(html_body):
    parser = LinkExtractor()
    parser.feed(html_body)
    return parser.links


def get_html_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                charset = part.get_content_charset() or 'utf-8'
                return part.get_payload(decode=True).decode(charset, errors='replace')
    else:
        charset = msg.get_content_charset() or 'utf-8'
        return msg.get_payload(decode=True).decode(charset, errors='replace')
    return ""


def follow_link(url):
    try:
        response = requests.get(url, timeout=15, allow_redirects=True)
        title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else None
        return {
            'status_code': response.status_code,
            'final_url': response.url,
            'page_title': title,
        }
    except Exception as e:
        return {'error': str(e)}


def check_inbox():
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("EMAIL_ADDRESS or EMAIL_PASSWORD not set", flush=True)
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select('INBOX')

        _, data = mail.search(None, f'(UNSEEN FROM "{TRIGGER_SENDER}")')
        mail_ids = data[0].split()

        if not mail_ids:
            mail.logout()
            return

        mail_id = mail_ids[0]
        _, msg_data = mail.fetch(mail_id, '(RFC822)')
        raw_email = msg_data[0][1]
        msg = email_lib.message_from_bytes(raw_email)

        subject = msg.get('Subject', '')
        sender = msg.get('From', '')

        if TRIGGER_SUBJECT not in subject:
            mail.logout()
            return

        html_body = get_html_body(msg)
        all_links = extract_links(html_body)

        target_keywords = ['bekijk aanvraag', 'accepteren']
        results = []
        for link in all_links:
            if any(kw in link['text'].lower() for kw in target_keywords) and link['url'].startswith('http'):
                response = follow_link(link['url'])
                results.append({
                    'link_text': link['text'],
                    'url': link['url'],
                    'response': response,
                })

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_entry = {
            'timestamp': timestamp,
            'subject': subject,
            'sender': sender,
            'links_followed': results,
        }

        log_file = LOG_DIR / f"{timestamp}.json"
        log_file.write_text(json.dumps(log_entry, indent=2, ensure_ascii=False))
        print(f"Processed email. Log saved to {log_file}", flush=True)

        mail.store(mail_id, '+FLAGS', '\\Seen')
        mail.logout()

    except Exception as e:
        print(f"Error checking inbox: {e}", flush=True)


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
        params = parse_qs(parsed.query)
        token = params.get("token", [None])[0]

        if parsed.path in ("/bot/activate", "/bot/deactivate"):
            if not BOT_TOKEN or token != BOT_TOKEN:
                self._send_json(403, {"detail": "Forbidden"})
                return
            if parsed.path == "/bot/activate":
                FLAG_FILE.parent.mkdir(parents=True, exist_ok=True)
                FLAG_FILE.touch()
                self._send_json(200, {"status": "activated"})
            else:
                if FLAG_FILE.exists():
                    FLAG_FILE.unlink()
                self._send_json(200, {"status": "deactivated"})
        else:
            self._send_json(404, {"detail": "Not found"})

    def log_message(self, format, *args):
        pass


def run_server():
    server = HTTPServer(("127.0.0.1", PORT), BotHandler)
    print(f"API server running on port {PORT}", flush=True)
    server.serve_forever()


def run_monitor():
    print("Email monitor started.", flush=True)
    while True:
        if FLAG_FILE.exists():
            check_inbox()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    run_monitor()
