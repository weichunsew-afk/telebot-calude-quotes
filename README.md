# Daily Quote/Story Telegram Bot — Setup

Sends you an inspirational quote or short story every day at 8:30am SGT for
365 days, via Telegram, with a "read" acknowledgment button. Runs entirely
on GitHub Actions — no server of your own required.

## 1. Create a Telegram bot

1. Open Telegram, message **@BotFather**.
2. Send `/newbot`, follow the prompts, and choose a name/username.
3. BotFather gives you a **bot token** — save it, you'll need it below.
4. Send your new bot any message (e.g. "hi") so it can see your chat.
5. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser
   and find `"chat":{"id": ...}` in the response — that number is your
   **chat ID**.

## 2. Get an Anthropic API key

Create one at [console.anthropic.com](https://console.anthropic.com) if you
don't already have one. This is a separate key from claude.ai — it's billed
per use, but 365 short generations on Sonnet will cost a few dollars total
for the whole year at most.

## 3. Create the GitHub repo

1. Create a new **private** GitHub repository.
2. Upload these files, keeping the folder structure:
   - `send_quote.py`
   - `check_reminder.py`
   - `telegram_utils.py`
   - `state.json`
   - `.github/workflows/daily-quote.yml`
   - `.github/workflows/check-reminder.yml`

## 4. Add your secrets

In the repo: **Settings → Secrets and variables → Actions → New repository secret**.
Add three secrets:

| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | the bot token from step 1 |
| `TELEGRAM_CHAT_ID` | the chat ID from step 1 |
| `ANTHROPIC_API_KEY` | your Anthropic API key from step 2 |

Both workflows read from the same repo secrets, so you only need to add these once. `check-reminder.yml` doesn't use `ANTHROPIC_API_KEY` (it doesn't generate content), but there's no harm in it being set.

## 5. Test it

Go to the **Actions** tab. You'll see two workflows: **Daily Quote** and
**Check Reminder**. Run **Daily Quote** manually first (via **Run workflow**,
using the `workflow_dispatch` trigger) — you should get a Telegram message
within a minute or two. Then, without tapping the "✅ I've read this" button,
manually run **Check Reminder** — you should get a nudge message.

## 6. Let it run

Once both manual tests work, do nothing else. Two schedules fire automatically
every day:

- **08:30 SGT (`cron: '30 0 * * *'`)** — `send_quote.py` runs. It checks for
  any acknowledgment that came in overnight, generates a new quote or short
  story, sends it with a fresh "✅ I've read this" button, and marks that
  message as the new pending one.
- **09:30 SGT (`cron: '30 1 * * *'`)** — `check_reminder.py` runs, one hour
  later. If you haven't tapped the button yet, it checks Telegram once more
  and, if still unacknowledged, sends a single reminder nudge. If you did
  acknowledge it, this step does nothing.

Any acknowledgment — whether it happens right away, after the 9:30 reminder,
or any time before the next day's 8:30 send — is picked up the next time
either script runs, since both poll Telegram's update history rather than
listening live.

After day 365, `send_quote.py` sends a completion message and stops sending
new content (the reminder workflow will also stop nudging, since there's no
new pending message). At that point you can delete the repo or disable both
workflows (**Actions → [workflow name] → ⋯ → Disable workflow**).

## Notes

- GitHub Actions' free tier includes 2,000 minutes/month for private repos —
  these jobs take well under a minute a day combined, so cost isn't a concern.
- Only one reminder is sent per day, one hour after the message. It won't
  nag you repeatedly.
- **Quotes are original, not sourced.** Every third day you get a short
  story; the other days you get an original line composed by Claude for
  that day, with no attribution to any real person. Earlier versions asked
  for a quote plus "who said it," which risked fabricated or misattributed
  sourcing — that's been removed. If you'd rather pull from a verified
  quotes database instead (e.g. an API of real, sourced quotes) and reserve
  generation for the stories only, that's a bigger change but doable.
- If you'd rather the bot *pause* and stop sending new content entirely
  until you acknowledge (a hard stop instead of "starting fresh anyway"),
  that's a small change to `send_quote.py` — happy to adjust it if you want
  that behavior instead.
