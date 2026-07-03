# Daily Quote/Story Telegram Bot — Setup

Sends you a real, sourced quote or a Claude-generated short story every day
at 8:30am SGT for 365 days, via Telegram, with a "read" acknowledgment
button that gives near-instant feedback when tapped. Runs entirely on
GitHub Actions — no server of your own required.

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
don't already have one. This is separate from your claude.ai login — it's
billed per use, but this only calls the API on story days (roughly every
third day), so total cost for the year is a couple of dollars at most.

## 3. Create the GitHub repo

1. Create a new **private** GitHub repository.
2. Upload these files, keeping the folder structure exactly:
   ```
   README.md
   send_quote.py
   check_reminder.py
   poll_ack.py
   telegram_utils.py
   state.json
   leader_quotes.json
   .github/workflows/daily-quote.yml
   .github/workflows/check-reminder.yml
   .github/workflows/poll-ack.yml
   ```
   The two `.yml` files must be created with the path typed directly into
   the filename (e.g. `.github/workflows/daily-quote.yml`) — GitHub creates
   the folders automatically when it sees the slashes.

## 4. Add your secrets

In the repo: **Settings → Secrets and variables → Actions → New repository secret**.
Add three secrets:

| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | the bot token from step 1 |
| `TELEGRAM_CHAT_ID` | the chat ID from step 1 |
| `ANTHROPIC_API_KEY` | your Anthropic API key from step 2 |

All three workflows read from the same repo secrets — add these once.
`check-reminder.yml` and `poll-ack.yml` don't use `ANTHROPIC_API_KEY`, but
there's no harm in it being set for all of them.

## 5. Test it

Go to the **Actions** tab. You'll see three workflows: **Daily Quote**,
**Check Reminder**, and **Poll Acknowledgment**.

1. Run **Daily Quote** manually (**Run workflow** button). You should get a
   Telegram message with a "✅ I've read this" button within a minute or two.
2. Tap the button in Telegram.
3. Run **Poll Acknowledgment** manually. You should get a small confirmation
   popup on your phone, and the button should disappear from the message.
4. To test the reminder path: run **Daily Quote** again, this time *don't*
   tap the button, and run **Check Reminder** manually — you should get a
   nudge message.

## 6. Let it run

Once the manual tests work, do nothing else. Three schedules fire automatically:

- **08:30 SGT daily** — `send_quote.py`. Every third day it generates an
  original short story via Claude; other days it fetches a real, sourced
  quote (with genuine author) from a public quotes database. Sends it with
  a fresh "✅ I've read this" button.
- **09:30 SGT daily** — `check_reminder.py`, one hour later. If you haven't
  acknowledged yet, sends a single nudge. Won't repeat beyond that.
- **Every 15 minutes** — `poll_ack.py`. This is what makes tapping the
  button feel instant: as soon as it detects a tap, it sends a confirmation
  popup to your phone and removes the button from the message so it can't
  be tapped again. Most runs are a fast no-op (nothing pending), so this
  adds negligible cost.

After day 365, `send_quote.py` sends a completion message and stops. At
that point you can delete the repo or disable all three workflows
(**Actions → [workflow name] → ⋯ → Disable workflow**).

## Where the content comes from

- **Quotes** (roughly 2 of every 3 days): drawn from `leader_quotes.json`, a
  curated, static list of quotes from actual heads of state/government —
  presidents, prime ministers, monarchs — bundled directly in the repo
  rather than pulled from a live third-party API. This was a deliberate
  choice: a general-purpose quotes API has no reliable "world leaders"
  filter, and asking Claude to recall a leader's quote from memory
  reintroduces the exact misattribution risk this design avoids elsewhere.
  The script tracks which quote IDs you've seen (`seen_quote_ids` in
  `state.json`) and avoids repeats until the pool (currently 40 quotes) is
  exhausted, then cycles again.
  **Caveat**: this list was written from general knowledge, not
  independently fact-checked line by line. One entry was caught and fixed
  during creation (a movie line that had been mistakenly attributed to
  Churchill), which is a useful reminder that even a "curated" list from a
  model isn't infallible — if a specific quote matters for something
  important, worth a quick independent check.
- **Short stories** (roughly 1 of every 3 days): generated fresh by Claude
  (`claude-sonnet-4-6`) as original creative writing — no attribution
  claims involved, so no misattribution risk.

## Notes

- GitHub Actions' free tier includes 2,000 minutes/month for private repos.
  Even with three schedules (including a 15-minute poll), this stays well
  under that limit — the poll job is a fast no-op almost every time it runs.
- **Commit race conditions**: with three workflows writing to `state.json`
  on different schedules, occasional push conflicts are expected (two jobs
  finishing around the same time). Each workflow commits its local change
  first, then pulls with rebase and pushes, retrying up to 5 times with a
  short delay — this handles the normal case. If you ever see a workflow
  fail on the commit step after all retries, it means two jobs collided
  very close together; just re-run the failed one.
- If you'd rather the bot *pause* and stop sending new content entirely
  until you acknowledge (a hard stop instead of "starting fresh anyway"),
  that's a small change to `send_quote.py` — happy to adjust it if you want
  that behavior instead.
