"""
Sends one daily quote or short story to Telegram, and stops automatically
after 365 days.

Run once per day at 8:30am SGT by
.github/workflows/daily-quote.yml
"""

import json
import os
import random

import anthropic

from telegram_utils import check_acknowledgment, load_state, save_state, send_message

TOTAL_DAYS = 365
LEADER_QUOTES_FILE = "leader_quotes.json"


def load_quote_pool():
    with open(LEADER_QUOTES_FILE) as f:
        return json.load(f)


def fetch_quote(seen_ids):
    """Pick a quote from the curated world-leaders pool that hasn't been
    sent yet. Once the whole pool has been used, resets and allows repeats
    rather than failing.

    Returns (quote_text, author, context, quote_id, seen_ids_reset: bool)
    """
    pool = load_quote_pool()
    unseen = [q for q in pool if q["id"] not in seen_ids]

    was_reset = False
    if not unseen:
        unseen = pool
        was_reset = True

    q = random.choice(unseen)
    return q["quote"], q["author"], q.get("context", ""), q["id"], was_reset


def generate_story(client, day):
    prompt = (
        "Write a short inspirational story, 150-200 words. "
        f"This is day {day} of a 365-day daily series, so it should feel "
        "fresh and avoid cliche tropes. Return only the story itself, no "
        "preamble or labels."
    )
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def main():
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    api_key = os.environ["ANTHROPIC_API_KEY"]

    state = load_state()

    if state["day"] >= TOTAL_DAYS:
        send_message(bot_token, chat_id, "You made it through all 365 days. 🎉", with_ack_button=False)
        print("Series complete — you can disable the workflow schedules now.")
        return

    # Catch any late ack that came in after the last poll but before now.
    found_ack, new_last_id = check_acknowledgment(bot_token, state["last_update_id"])
    state["last_update_id"] = new_last_id
    was_acknowledged = state["acknowledged"] or found_ack

    next_day = state["day"] + 1

    if next_day % 3 == 0:
        client = anthropic.Anthropic(api_key=api_key)
        content = generate_story(client, next_day)
    else:
        quote, author, context, quote_id, was_reset = fetch_quote(state["seen_quote_ids"])
        if was_reset:
            state["seen_quote_ids"] = [quote_id]
        else:
            state["seen_quote_ids"].append(quote_id)
        attribution = f"— {author}, {context}" if context else f"— {author}"
        content = f'"{quote}"\n\n{attribution}'

    note = ""
    if not was_acknowledged and next_day > 1:
        note = "(Yesterday's message went unacknowledged — starting fresh today.)\n\n"

    message_id = send_message(bot_token, chat_id, f"Day {next_day}/{TOTAL_DAYS}\n\n{note}{content}")

    state["day"] = next_day
    state["acknowledged"] = False  # this new message is now the pending one
    state["last_message_id"] = message_id
    state["last_chat_id"] = chat_id
    save_state(state)
    print(f"Sent day {next_day}. Previous day acknowledged: {was_acknowledged}")


if __name__ == "__main__":
    main()

