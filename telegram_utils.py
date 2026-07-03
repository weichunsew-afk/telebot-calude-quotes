"""Shared Telegram + state helpers used by send_quote.py, check_reminder.py,
and poll_ack.py"""

import json
import os

import requests

STATE_FILE = "state.json"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
    else:
        state = {}
    state.setdefault("day", 0)
    state.setdefault("last_update_id", 0)
    state.setdefault("acknowledged", True)
    state.setdefault("seen_quote_ids", [])
    state.setdefault("last_message_id", None)
    state.setdefault("last_chat_id", None)
    return state


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_updates(bot_token, last_update_id):
    """Fetch raw Telegram updates since last_update_id."""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    resp = requests.get(url, params={"offset": last_update_id + 1, "timeout": 5})
    resp.raise_for_status()
    return resp.json().get("result", [])


def check_acknowledgment(bot_token, last_update_id):
    """Poll Telegram for any '✅ I've read this' button tap since last_update_id.

    Returns (found_ack: bool, new_last_update_id: int).
    """
    updates = get_updates(bot_token, last_update_id)

    found_ack = False
    new_last_id = last_update_id
    for u in updates:
        new_last_id = max(new_last_id, u["update_id"])
        if u.get("callback_query", {}).get("data") == "ack":
            found_ack = True
    return found_ack, new_last_id


def send_message(bot_token, chat_id, text, with_ack_button=True):
    """Sends a message. Returns the sent message's message_id."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if with_ack_button:
        payload["reply_markup"] = json.dumps(
            {"inline_keyboard": [[{"text": "✅ I've read this", "callback_data": "ack"}]]}
        )
    resp = requests.post(url, data=payload)
    resp.raise_for_status()
    return resp.json()["result"]["message_id"]


def answer_callback_query(bot_token, callback_query_id, text):
    """Shows a small confirmation popup on the user's device."""
    url = f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery"
    requests.post(url, data={"callback_query_id": callback_query_id, "text": text})


def remove_ack_button(bot_token, chat_id, message_id):
    """Removes the inline button so it can't be tapped again."""
    url = f"https://api.telegram.org/bot{bot_token}/editMessageReplyMarkup"
    resp = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": json.dumps({"inline_keyboard": []}),
        },
    )
    # Telegram errors if the markup is already gone (e.g. edited twice) —
    # that's harmless here, so don't raise on it.
    if not resp.ok:
        print(f"Note: could not edit message markup ({resp.status_code}): {resp.text}")
