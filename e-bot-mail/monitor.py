import imaplib
import email as email_lib
import re
import json
import os
import requests
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser

ROOT = Path(__file__).parent.parent
FLAG_FILE = ROOT / "e-bot-mail" / "active"
LOG_DIR = ROOT / "e-bot-mail" / "logs"

IMAP_SERVER = os.environ.get("EMAIL_IMAP_SERVER", "webreus.email")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

TRIGGER_SENDER = "noreply@deimmowinkel.be"
TRIGGER_SUBJECT = "Nieuwe keuringsaanvraag"


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


def run():
    if not FLAG_FILE.exists():
        return

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("EMAIL_ADDRESS or EMAIL_PASSWORD not set in environment")
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
        print(f"Done. Log saved to {log_file}")

        mail.store(mail_id, '+FLAGS', '\\Seen')
        mail.logout()

    except Exception as e:
        print(f"Error: {e}")
        return

    FLAG_FILE.unlink()


if __name__ == '__main__':
    run()
