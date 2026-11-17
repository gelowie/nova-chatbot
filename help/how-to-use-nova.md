# How to use Nova

## In the browser

1. Start the server (`python server.py`) and open <http://127.0.0.1:8000>.
2. Type a message (up to 500 characters) and press **Enter**, or click the send button. The input is a single line.
3. Click a **quick-reply chip** under Nova's message to send a suggested follow-up.
4. Use the **clear** (trash) button in the header to empty the conversation. Nova greets you again. Nothing is saved between page loads.

Replies can contain **bold** text and `code`; everything else is plain text. While Nova is answering, the input is disabled and the header shows "Nova is typing…".

## What to ask

### Math (answered by `math_solver.py`)

| You type | Nova answers |
|---|---|
| `whats 5 plus 3 times 2` | Solved **5 + 3 × 2** = **11** |
| `144 divided by 12` | Solved **144 ÷ 12** = **12** |
| `15% of 200` or `15 percent of 200` | Solved **(15 ÷ 100) × 200** = **30** |
| `2^10`, `2 ** 10` | = **1024** |
| `(12 + 8) / 4`, `-5 + 10` | = **5** |
| `5 x 3`, `5 × 3` | = **15** |
| `3 squared plus 4 squared` | = **25** |
| `2 cubed` | = **8** |
| `20 modulo 7`, `20 mod 7`, `20 % 7` | = **6** |
| `1,000 + 1` | = **1001** |
| `hey nova please calculate 6 times 7` | = **42** |
| `100 / 0` | A friendly message instead of a crash |

Words understood: plus, minus, times, multiplied by, divided by, over, take away, added to, modulo, mod, to the power of, power, squared, cubed, percent and "x" between numbers, plus leading filler such as "what is", "calculate" and "can you". Whole numbers are printed in full; other results keep up to 10 significant digits (`1/3` → `0.3333333333`).

What does **not** work as math: a bare number (`5`), a trailing operator (`5+`), anything with leftover words (`2 + abc`), scientific notation (`1e5`) and exponents above 64.

### Time and dates (answered by `time_reader.py`)

`what time is it` · `tell me the time` · `what is the date` · `what day is it` · `what is tomorrow` · `what day is tomorrow` · `what was yesterday` · `what is the date next month` · `what was the date last month` · `what will the date be in 3 weeks` · `date in 5 days` · `in 2 months` · `3 weeks from now` · `full date and time`

Offsets of up to 10,000 days, weeks or months are supported. Times and dates come from the clock of the computer running the server (24-hour format; no time zones). Month arithmetic clamps to the end of the month (31 Jan + 1 month = 28 Feb, or 29 in a leap year).

Ordinary chat that merely mentions a day is **not** treated as a date question: `see you tomorrow` is a goodbye, `i have 2 days off` is chat.

### Conversation (answered by the JSON brain)

| Topic | Try |
|---|---|
| Greetings and goodbyes | `hello`, `good morning`, `what's up`, `bye` |
| About Nova | `who are you`, `what is your name`, `how old are you`, `who made you` |
| How you feel | `i am sad`, `i am happy`, `i am bored`, `i am tired`, `i need motivation` |
| Entertainment | `tell me a joke`, `fun fact`, `give me a quote`, `riddle`, `sing a song` |
| Advice | `study tips`, `career advice`, `save money`, `health tips`, `travel tips`, `i need advice` |
| Tech | `what is python`, `what is javascript`, `teach me to code`, `what is ai` |
| Recommendations | `recommend music`, `recommend a movie`, `recommend a book`, `video games`, `what should i eat` |
| Help | `help` or `what can you do` shows Nova's own summary |

Each topic understands several different phrasings; see the `patterns` of the matching intent in [the JSON brain](the-json-brain.md) to learn them, or add your own.

Typos and slang work: `helo`, `hru`, `sup`, `thx`, `wat r u doin`, `helloooo thereeee`.

Anything else gets a fallback reply with suggestions. Nova does not remember your earlier messages, so each message needs to make sense on its own.

## Using the API directly

The server exposes these routes:

| Route | Purpose |
|---|---|
| `GET /` | The chat page. |
| `GET /health` | Returns `{"ok":true}`. |
| `GET /docs/img/icon.png` | Nova's avatar (the only static file served). |
| `POST /chat` | Send `{"message": "..."}`, receive Nova's reply. |

```bash
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what day is it"}'
```

Response format:

```json
{
  "text": "Today is **Wednesday** — Wednesday, 11 November 2026 (2026-11-11).",
  "skill": "time",
  "suggestions": ["Tell me a joke", "What can you do?", "What time is it?"]
}
```

| Field | Meaning |
|---|---|
| `text` | The reply text (may contain `**bold**` and `` `code` ``). |
| `skill` | Which layer answered: `math`, `time`, `brain` or `fallback` (or `error` if something unexpected failed). |
| `suggestions` | Quick-reply suggestions for the UI. |

Errors: `400` for invalid JSON, a body that is not an object, a `message` that is not a string, or an invalid `Content-Length`; `413` for a body over 64 KiB; `404` for unknown paths. Error bodies look like `{"error": "..."}`.

An empty or missing `message` is not an error: it returns a fallback reply with `skill: "fallback"`.

The server accepts requests from any web page (`Access-Control-Allow-Origin: *`), but it only listens on `127.0.0.1`, so other computers cannot reach it.

### From Python

```python
import json
import urllib.request

req = urllib.request.Request(
    "http://127.0.0.1:8000/chat",
    data=json.dumps({"message": "15% of 200"}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as resp:
    print(json.load(resp)["text"])     # Solved **(15 ÷ 100) × 200** = **30**
```

### Without the server

You can also use the engine directly from Python, from the repository root:

```python
from src.py import NovaEngine

nova = NovaEngine("src/json/brain.json")
print(nova.respond("whats 5 plus 3 times 2"))
```
