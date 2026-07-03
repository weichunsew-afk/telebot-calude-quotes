"""
Runs every 15 minutes. If the pending message's button has been tapped,
shows a confirmation popup on the user's phone and removes the button so
it can't be tapped again. This is what makes acknowledgment feel immediate
instead of waiting for the once-a-day checks in send_quote.py / check_reminder.py.

Run on a schedule by
.github/workflows/poll-ack.yml
"""

import os

from telegram_utils import (
    answer_callback_query,
    get_updates,
    load_state,
    remove_ack_button,
    save_state,
)


def main():
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]

    state = load_state()

    if state["acknowledged"]:
        print("Nothing pending, nothing to do.")
        return

    updates = get_updates(bot_token, state["last_update_id"])
    new_last_id = state["last_update_id"]
    got_ack = False

    for u in updates:
        new_last_id = max(new_last_id, u["update_id"])
        cq = u.get("callback_query")
        if cq and cq.get("data") == "ack":
            answer_callback_query(bot_token, cq["id"], "✅ Marked as read — thanks!")
            got_ack = True

    state["last_update_id"] = new_last_id

    if got_ack:
        state["acknowledged"] = True
        if state.get("last_chat_id") and state.get("last_message_id"):
            remove_ack_button(bot_token, state["last_chat_id"], state["last_message_id"])
        print("Acknowledged — button removed.")
    else:
        print("No new acknowledgment yet.")

    save_state(state)


if __name__ == "__main__":
    main()
