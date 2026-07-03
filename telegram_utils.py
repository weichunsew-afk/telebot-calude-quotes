"""Shared Telegram + state helpers used by send_quote.py and check_reminder.py"""

import json
import os

import requests

STATE_FILE = "state.json"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"day": 0, "last_update_id": 0, "acknowledged": True}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def check_acknowledgment(bot_token, last_update_id):
    """Poll Telegram for any '✅ I've read this' button tap since last_update_id.

    Returns (found_ack: bool, new_last_update_id: int).
    """
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    resp = requests.get(url, params={"offset": last_update_id + 1, "timeout": 5})
    resp.raise_for_status()
    updates = resp.json().get("result", [])

    found_ack = False
    new_last_id = last_update_id
    for u in updates:
        new_last_id = max(new_last_id, u["update_id"])
        if u.get("callback_query", {}).get("data") == "ack":
            found_ack = True
    return found_ack, new_last_id


def send_message(bot_token, chat_id, text, with_ack_button=True):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if with_ack_button:
        payload["reply_markup"] = json.dumps(
            {"inline_keyboard": [[{"text": "✅ I've read this", "callback_data": "ack"}]]}
        )
    resp = requests.post(url, data=payload)
    resp.raise_for_status()
