# e-bot-mail

Standalone bot that monitors an IMAP inbox for trigger emails from deimmowinkel.be and automatically follows the action links inside them (e.g. "bekijk aanvraag", "accepteren"). Controlled via a simple HTTP API with activate/deactivate endpoints, which an iPhone Shortcut calls remotely.

---

## How it works

A single script (`bot.py`) runs two things simultaneously:

**HTTP server (always on)** — listens on port 8001. Manages a flag file (`e-bot-mail/active`) that acts as an on/off switch. The API is the only way to flip this switch.

**Email monitor loop (always on)** — polls the IMAP inbox every 30 seconds. When the flag is on, it connects to the inbox, finds unseen trigger emails, extracts links, follows them, and logs the result to `e-bot-mail/logs/`. When the flag is off, it does nothing and waits for the next poll.

The bot stays running permanently. You control its behavior via the API.

---

## Deployment

- **Server:** Bluehost VPS at `129.121.109.129`
- **Repo path on server:** `/opt/matchadaddy/RA/`
- **External URL:** `https://api.matchadaddy.uk/bot/...`
- **Nginx** reverse-proxies `/bot/` to `http://127.0.0.1:8001/bot/`
- **Managed by:** systemd service `e-bot-mail`

---

## Environment variables

Stored in `/opt/matchadaddy/RA/.env` on the server. Use `.env.example` in the repo root as a template.

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | Yes | — | Secret token required to call activate/deactivate |
| `BOT_PORT` | No | `8001` | Port the server listens on |
| `EMAIL_ADDRESS` | Yes | — | IMAP login email address |
| `EMAIL_PASSWORD` | Yes | — | IMAP login password |
| `EMAIL_IMAP_SERVER` | No | `webreus.email` | IMAP server hostname |

---

## API endpoints

All endpoints are available externally via `https://api.matchadaddy.uk`.

### GET `/bot/status`
Returns whether the bot is currently active (flag file exists).

```
GET /bot/status
→ {"active": true}
```

### POST `/bot/activate?token=TOKEN`
Turns on email processing.

```
POST /bot/activate?token=YOUR_TOKEN
→ {"status": "activated"}
```

### POST `/bot/deactivate?token=TOKEN`
Turns off email processing.

```
POST /bot/deactivate?token=YOUR_TOKEN
→ {"status": "deactivated"}
```

Returns `403` if the token is missing or wrong.

---

## Systemd service

`bot.py` runs as a systemd service so it starts automatically at boot and restarts if it crashes.

**Install the service (first time only):**
```bash
cp /opt/matchadaddy/RA/e-bot-mail/e-bot-mail.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable e-bot-mail
systemctl start e-bot-mail
```

**Common commands:**
```bash
systemctl status e-bot-mail      # check if running
systemctl restart e-bot-mail     # restart after code changes
systemctl stop e-bot-mail        # stop the bot
journalctl -u e-bot-mail -f      # live logs
```

**After pulling new code**, always restart the service to pick up changes:
```bash
git pull && systemctl restart e-bot-mail
```

---

## iPhone Shortcut

Shortcuts named "activeer" and "deactiveer" call `/bot/activate` and `/bot/deactivate` via POST requests with the token as a query parameter. They use the Dutch iOS Shortcuts action "Haal inhoud van URL" with method set to POST.

---

## Nightly git pull (cron)

A cron job pulls the latest code and CSV files from GitHub every night at 1:00 AM GMT:

```
0 1 * * * cd /opt/matchadaddy/RA && git pull >> /var/log/ra-pull.log 2>&1
```

After a pull that includes Python code changes, restart the service:
```bash
systemctl restart e-bot-mail
```

CSV file updates do not require a restart.

---

## Dependencies

Only one external dependency:

```
requests
```

The module is self-contained and does not depend on any other code in this repository.

---

## Trigger configuration

Defined as constants in `bot.py`:

| Constant | Value |
|---|---|
| `TRIGGER_SENDER` | `noreply@deimmowinkel.be` |
| `TRIGGER_SUBJECT` | `Nieuwe keuringsaanvraag` |
| `target_keywords` | `bekijk aanvraag`, `accepteren` |

Only unseen emails matching both sender and subject are processed. Only links whose text contains one of the target keywords are followed.
