"""
Sends one daily quote or short story to Telegram, and stops automatically
after 365 days.

Run once per day at 8:30am SGT by
.github/workflows/daily-quote.yml
"""

import anthropic

from telegram_utils import check_acknowledgment, load_state, save_state, send_message

TOTAL_DAYS = 365


def generate_content(client, day):
    if day % 3 == 0:
        kind = "a short inspirational story, 150-200 words"
        instruction = (
            f"Write {kind}. This is day {day} of a 365-day daily series, so it "
            "should feel fresh and avoid cliche tropes. "
            "Return only the story itself, no preamble or labels."
        )
    else:
        kind = "a single original inspirational line, 1-2 sentences"
        instruction = (
            f"Write {kind}. This is day {day} of a 365-day daily series, so it "
            "should feel fresh and avoid the most overused/cliche phrasing. "
            "This must be an ORIGINAL line you compose yourself — do not "
            "attribute it to any real person, living or dead, and do not "
            "imply it is a known/existing quote. Write it as a standalone "
            "thought with no attribution at all. "
            "Return only the line itself, no preamble, labels, or quotation marks."
        )

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": instruction}],
    )
    return msg.content[0].text.strip()


def main():
    import os

    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    api_key = os.environ["ANTHROPIC_API_KEY"]

    state = load_state()

    if state["day"] >= TOTAL_DAYS:
        send_message(bot_token, chat_id, "You made it through all 365 days. 🎉", with_ack_button=False)
        print("Series complete — you can disable the workflow schedules now.")
        return

    # Catch any late ack that came in after the reminder check but before now.
    found_ack, new_last_id = check_acknowledgment(bot_token, state["last_update_id"])
    state["last_update_id"] = new_last_id
    was_acknowledged = state["acknowledged"] or found_ack

    next_day = state["day"] + 1
    client = anthropic.Anthropic(api_key=api_key)
    content = generate_content(client, next_day)

    note = ""
    if not was_acknowledged and next_day > 1:
        note = "(Yesterday's message went unacknowledged — starting fresh today.)\n\n"

    send_message(bot_token, chat_id, f"Day {next_day}/{TOTAL_DAYS}\n\n{note}{content}")

    state["day"] = next_day
    state["acknowledged"] = False  # this new message is now the pending one
    save_state(state)
    print(f"Sent day {next_day}. Previous day acknowledged: {was_acknowledged}")


if __name__ == "__main__":
    main()
