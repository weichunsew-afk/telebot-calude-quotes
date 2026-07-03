"""
Runs 1 hour after send_quote.py. Checks whether today's message has been
acknowledged; if not, sends a single reminder.

Run once per day at 9:30am SGT by
.github/workflows/check-reminder.yml
"""

import os

from telegram_utils import check_acknowledgment, load_state, save_state, send_message


def main():
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    state = load_state()

    if state["day"] == 0:
        print("No message has been sent yet — nothing to check.")
        return

    if state["acknowledged"]:
        print("Already acknowledged, nothing to do.")
        return

    found_ack, new_last_id = check_acknowledgment(bot_token, state["last_update_id"])
    state["last_update_id"] = new_last_id

    if found_ack:
        state["acknowledged"] = True
        save_state(state)
        print("Acknowledged just in time — no reminder needed.")
        return

    send_message(
        bot_token,
        chat_id,
        f"👋 Reminder: you haven't confirmed reading day {state['day']}'s message yet.",
        with_ack_button=True,
    )
    save_state(state)
    print("Sent reminder.")


if __name__ == "__main__":
    main()
