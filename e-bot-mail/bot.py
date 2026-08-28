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
LAST_UID_FILE = ROOT / "e-bot-mail" / "last_uid.txt"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("BOT_PORT", 8001))
IMAP_SERVER = os.environ.get("EMAIL_IMAP_SERVER", "webreus.email")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

ACCOUNT_EMAIL = os.environ.get("ACCOUNT_EMAIL")
ACCOUNT_PASSWORD = os.environ.get("ACCOUNT_PASSWORD")

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


def _extract_attr(tag_html, attr):
    m = re.search(rf'{attr}="([^"]*)"', tag_html)
    return m.group(1) if m else None


def compute_antibot_key(key):
    """Replicate the Antibot module's client-side key transformation.

    From antibot.js: reverse the whole key, split into 2-char chunks,
    reverse each chunk, then join. Purely deterministic, no JS needed.
    """
    reversed_full = key[::-1]
    chunks = [reversed_full[i:i + 2] for i in range(0, len(reversed_full), 2)]
    return ''.join(chunk[::-1] for chunk in chunks)


def submit_antibot_form(session, html, page_url, form_html_id):
    """Find an Antibot-protected form by its HTML id and submit it directly,
    computing the antibot_key the way antibot.js would after a real mousemove."""
    for tag_match in re.finditer(r'<form([^>]*)>(.*?)</form>', html, re.DOTALL):
        tag_attrs, form_body = tag_match.groups()
        if _extract_attr(tag_attrs, 'id') != form_html_id:
            continue

        data_action = _extract_attr(tag_attrs, 'data-action')
        if not data_action:
            return None

        settings_match = re.search(
            r'"antibot":\{"forms":\{"' + re.escape(form_html_id) + r'":\{"id":"[^"]*","key":"([^"]+)"\}',
            html,
        )
        if not settings_match:
            return None

        antibot_key = compute_antibot_key(settings_match.group(1))

        fields = {}
        for name, value in re.findall(r'name="([^"]+)"[^>]*value="([^"]*)"', form_body):
            fields[name] = value
        for value, name in re.findall(r'value="([^"]*)"[^>]*name="([^"]+)"', form_body):
            fields.setdefault(name, value)
        fields['antibot_key'] = antibot_key

        parsed_page = urlparse(page_url)
        action_url = data_action if data_action.startswith('http') else f"{parsed_page.scheme}://{parsed_page.netloc}{data_action}"
        return session.post(action_url, data=fields, timeout=15, allow_redirects=True)

    return None


def follow_link_authenticated(url, timestamp):
    """Follow a link, logging in if redirected to a login page, and save the final page content."""
    if not ACCOUNT_EMAIL or not ACCOUNT_PASSWORD:
        return {'error': 'ACCOUNT_EMAIL or ACCOUNT_PASSWORD not set'}

    session = requests.Session()
    try:
        response = session.get(url, timeout=15, allow_redirects=True)

        if 'user/login' in response.url:
            form_build_match = re.search(r'name="form_build_id"\s+value="([^"]+)"', response.text)
            if not form_build_match:
                return {'error': 'Could not find form_build_id on login page'}

            parsed_login = urlparse(response.url)
            params = parse_qs(parsed_login.query)
            destination = params.get('destination', [None])[0]

            login_url = f"{parsed_login.scheme}://{parsed_login.netloc}{parsed_login.path}"
            if destination:
                login_url += f"?destination={destination}"

            login_data = {
                'name': ACCOUNT_EMAIL,
                'pass': ACCOUNT_PASSWORD,
                'form_build_id': form_build_match.group(1),
                'form_id': 'user_login_form',
                'op': 'Inloggen',
            }
            response = session.post(login_url, data=login_data, timeout=15, allow_redirects=True)

            # The login form's own redirect doesn't always honor `destination`
            # (some Drupal setups resolve it client-side via JS after login).
            # Explicitly re-fetch the destination page now that the session
            # is authenticated, so the approve action actually gets triggered.
            if destination and 'user/login' not in response.url:
                destination_url = f"{parsed_login.scheme}://{parsed_login.netloc}{destination}"
                response = session.get(destination_url, timeout=15, allow_redirects=True)

        if 'inspection-request-confirmation-form' in response.text:
            submit_response = submit_antibot_form(
                session, response.text, response.url, 'inspection-request-confirmation-form'
            )
            if submit_response is not None:
                response = submit_response

        title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else None

        content_file = LOG_DIR / f"{timestamp}_accepteren.html"
        content_file.write_text(response.text, encoding='utf-8')

        return {
            'status_code': response.status_code,
            'final_url': response.url,
            'page_title': title,
            'content_saved_to': str(content_file),
        }
    except Exception as e:
        return {'error': str(e)}


def get_last_uid():
    if LAST_UID_FILE.exists():
        return int(LAST_UID_FILE.read_text().strip())
    return None


def save_last_uid(uid):
    LAST_UID_FILE.write_text(str(uid))


def process_message(mail, uid, msg):
    subject = msg.get('Subject', '')
    sender = msg.get('From', '')

    if TRIGGER_SUBJECT not in subject:
        return

    html_body = get_html_body(msg)
    all_links = extract_links(html_body)

    target_keywords = ['bekijk aanvraag', 'accepteren']
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    results = []
    for link in all_links:
        if any(kw in link['text'].lower() for kw in target_keywords) and link['url'].startswith('http'):
            if 'accepteren' in link['text'].lower():
                response = follow_link_authenticated(link['url'], timestamp)
            else:
                response = follow_link(link['url'])
            results.append({
                'link_text': link['text'],
                'url': link['url'],
                'response': response,
            })

    log_entry = {
        'timestamp': timestamp,
        'subject': subject,
        'sender': sender,
        'links_followed': results,
    }

    log_file = LOG_DIR / f"{timestamp}.json"
    log_file.write_text(json.dumps(log_entry, indent=2, ensure_ascii=False))
    print(f"Processed email. Log saved to {log_file}", flush=True)

    mail.uid('store', uid, '+FLAGS', '\\Seen')


def check_inbox():
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("EMAIL_ADDRESS or EMAIL_PASSWORD not set", flush=True)
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select('INBOX')

        _, data = mail.uid('search', None, f'(FROM "{TRIGGER_SENDER}")')
        uids = [int(u) for u in data[0].split()]

        if not uids:
            mail.logout()
            return

        last_uid = get_last_uid()

        if last_uid is None:
            # First run: seed to the current newest UID so we don't process the historical backlog.
            save_last_uid(max(uids))
            mail.logout()
            return

        new_uids = sorted(u for u in uids if u > last_uid)

        for uid in new_uids:
            _, msg_data = mail.uid('fetch', str(uid), '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email_lib.message_from_bytes(raw_email)
            try:
                process_message(mail, str(uid), msg)
            except Exception as e:
                print(f"Error processing email uid {uid}: {e}", flush=True)
            save_last_uid(uid)

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
