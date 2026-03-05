import os
import json
import concurrent.futures
from datetime import datetime


def _log_input_task(id, name, log_type="artist_logs"):
    creds_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        return
    import pygsheets
    creds = json.loads(creds_json)
    if "private_key" in creds:
        creds["private_key"] = creds["private_key"].replace("\\n", "\n")
    gc = pygsheets.authorize(service_account_json=json.dumps(creds))
    sh = gc.open_by_key("1fgSX9Z8qlpAm_ZVE-CCtsvn2IZV-PmnQ8UfP2g60HfY")
    wks = sh.worksheet_by_title(log_type)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    wks.append_table([id, name, timestamp], start='A1', dimension='ROWS', overwrite=False)


def log_input(id, name, log_type="artist_logs", timeout=2):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(_log_input_task, id, name, log_type)
        try:
            return future.result(timeout=timeout)
        except Exception:
            return None
