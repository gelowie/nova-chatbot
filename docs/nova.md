# Nova — architecture and components

Nova is a self-hosted, offline chatbot built from a hand-written **JSON brain**, small **local Python skills** for exact answers, a tiny **HTTP server** and a single-file **browser frontend**. It uses only the Python standard library. Repository: <https://github.com/gelowie/nova-chatbot>.

See also: [what is Nova?](../help/what-is-nova.md) · [why it exists](../help/why-nova.md) · [is it any good?](../help/is-nova-good.md) · [the JSON brain](../help/the-json-brain.md).

## Contents

- [Architecture](#architecture)
- [A message's journey](#a-messages-journey)
- [Components](#components)
- [The engine](#the-engine)
- [The math skill](#the-math-skill)
- [The time skill](#the-time-skill)
- [The server](#the-server)
- [The frontend](#the-frontend)
- [Design decisions](#design-decisions)
- [The Java implementation](#the-java-implementation)
- [Tests](#tests)
- [Current limitations](#current-limitations)
- [Extending Nova](#extending-nova)

## Architecture

```
 Browser (src/index.html)
        │  POST /chat  {"message": "..."}
        ▼
 server.py ── ThreadingHTTPServer on 127.0.0.1:8000
        │
        ▼
 src/py/engine.py  NovaEngine.respond(message)
        │
        ├─ 1. math_solver.solve(message)   → exact arithmetic        skill = "math"
        ├─ 2. time_reader.handle(message)  → clock / date answers    skill = "time"
        ├─ 3. JSON brain (src/json/brain.json)
        │       normalize → score patterns → best intent ≥ 0.35      skill = "brain"
        └─ 4. fallback message                                       skill = "fallback"
        │
        ▼
 {"text": "...", "skill": "...", "suggestions": [...]}
```

The first layer that produces an answer wins. Skills run before the brain so that exact questions (`5 + 5`) are computed, not fuzzy-matched.

## A message's journey

Following `whats 5 plus 3 times 2` from keyboard to screen:

1. **Frontend.** `src/index.html` trims the text, shows it as your bubble, clears the quick-reply chips, shows the typing indicator and sends `POST /chat` with `{"message": "whats 5 plus 3 times 2"}`.
2. **Server.** `server.py` checks the path, the `Content-Length` (rejecting anything over 64 KiB), parses the JSON body, checks that `message` is a string and calls `engine.respond(message)`.
3. **Engine.** `respond()` trims the message. An empty message gets a fallback; otherwise the skills run in order. The math skill answers.
4. **Math skill.** Filler words are stripped (`whats`), word operators become symbols (`plus` → `+`, `times` → `*`), the result `5 + 3 * 2` passes the validation gates, is parsed into a syntax tree and evaluated to `11`.
5. **Reply.** The engine returns `{"text": "Solved **5 + 3 × 2** = **11**", "skill": "math", "suggestions": ["Tell me a joke", "What can you do?", "What time is it?"]}`.
6. **Frontend again.** The page hides the typing indicator, renders the text (escaping HTML first, then turning `**bold**`, `` `code` `` and line breaks into markup), and draws the chips.

For a chat message such as `helo`, steps 3–5 differ: both skills return `None`, the brain corrects `helo` → `hello`, scores it against every pattern, picks the `greeting` intent and returns one of its replies.

## Components

| Component | File(s) | Role |
|---|---|---|
| Engine | `src/py/engine.py` | Loads the brain, normalizes text, routes messages, picks replies. Normalizes and compiles all patterns once at startup. |
| Math skill | `src/py/math_solver.py` | Turns words and symbols into an expression and evaluates it by walking a restricted syntax tree (never `eval()`). |
| Time skill | `src/py/time_reader.py` | Current time, date, weekday, tomorrow/yesterday, next/last month and offsets such as "in 3 weeks". |
| Package marker | `src/__init__.py`, `src/py/__init__.py` | Make `src` and `src.py` regular packages; `src/py/__init__.py` exports `NovaEngine`. |
| JSON brain | `src/json/brain.json` | 62 intents, 428 patterns, 211 replies, 61 phrase fixes, 127 typo fixes. See [the JSON brain](../help/the-json-brain.md). |
| Server | `server.py` | Serves `src/index.html`, `/health`, the icon, and `POST /chat`. Binds to `127.0.0.1` only. |
| Frontend | `src/index.html` | Chat UI: typing indicator, quick-reply chips, timestamps, clear button, responsive layout. |
| Java implementation | `src/java/` | Java versions of the math and time skills plus a command-line demo (`nova.NovaEngine`). |
| Tests | `tests/test_nova.py` | Standard-library `unittest` suite for the brain, skills, engine and server. |
| Documentation | `docs/`, `help/` | This overview, platform notes, translations, images, and the user and developer guides. |

## The engine

`NovaEngine(brain_path)` does its heavy lifting once, in `__init__`:

1. Reads `brain.json`.
2. Merges `phraseFixes` and `typos` into one dictionary (`_fixes`).
3. Normalizes every intent pattern and stores it with its word set and a compiled "appears in the message" regular expression.

`respond(message)` then returns a dict with `text`, `skill` and `suggestions`. Skill replies get a default set of three chips; brain replies use the intent's own `suggestions` when it has them; fallbacks use `meta.unknownSuggestions`.

**Normalization** (`_normalize`): lowercase; every character other than `a-z`, `0-9`, `'` and whitespace becomes a space; each fix is applied as a whole word, longest first (so `i luv u` is handled before `luv u`); whitespace is collapsed.

**Scoring** (`_match_intent`), for every pattern:

1. `overlap` = shared words ÷ all distinct words in message and pattern (Jaccard similarity).
2. If the pattern appears in the message on word boundaries, `overlap` becomes at least **0.95**. The pattern's last letter may be repeated, so `heyyy` still contains `hey`, but `this` does not contain `hi` and `you` does not contain `yo`.
3. `score = overlap × intent.priority` (priority defaults to 1).

The highest score wins, and ties go to the pattern that appears first in the file. A score below **0.35** means "no match" and leads to the fallback.

**Reply selection** (`_pick`): a random response, re-drawn (up to 12 times) if it equals the last one given for that intent. The "last reply" memory is global to the running server, not per user.

## The math skill

`math_solver.solve(text)` returns a formatted answer or `None`. Pipeline:

1. Lowercase, remove thousands commas, drop `?`, `!` and `=`, turn `÷`/`×` into `/`/`*`.
2. Strip up to six leading filler phrases (`hey`, `nova`, `please`, `can you`, `what is`, `calculate`, `tell me`, …).
3. Rewrite `15% of 200` and `15 percent of 200` as `(15/100)*200`, and `5 x 3` as `5 * 3` (the `x` only between digits).
4. Replace word operators with symbols: `to the power of`, `multiplied by`, `divided by`, `take away`, `added to`, `squared`, `cubed`, `plus`, `minus`, `times`, `over`, `modulo`, `mod`, `power`, `percent`.
5. **Validation gates** — the text must contain a digit, at least one operator, and *only* digits, spaces and `+ - * / % ^ ( ) .`. Anything else (a stray word, `1e5`) means "not math" and the message moves on to the next layer.
6. Parse with `ast.parse(..., mode="eval")` and evaluate recursively. Only numeric constants, `+ - * / // % **` and unary `+`/`-` are allowed; any other node type is rejected.
7. Safety limits: division, floor division or modulo by zero returns a friendly message; an exponent whose absolute value is above 64 is refused (so `9**9**9` cannot exhaust memory); results too large to print return "too large to display".
8. Formatting: integers are printed in full (never `1e+06`); other numbers keep up to 10 significant digits (`1/3` → `0.3333333333`).

## The time skill

`time_reader.handle(text)` checks these rules **in order**; the first that matches answers:

| # | Rule | Example |
|---|---|---|
| 1 | Relative offset with a cue (`in/after/add N units`, the word `date`, `from now/today`), capped at 10,000 | `date in 5 days`, `3 weeks from now` |
| 2 | Date and time | `date and time`, `full date`, `timestamp` |
| 3 | Tomorrow / yesterday, with a question cue or alone | `what is tomorrow`, `what day is tomorrow`, `yesterday's date` |
| 4 | Weekday | `what day is it` |
| 5 | Next month | `what is the date next month` |
| 6 | Last month | `what was the date last month` |
| 7 | Current time | `what time is it`, `time?` |
| 8 | Current date (broadest, so last) | `what is the date`, `what is today` |

Month arithmetic clamps to the end of the month **once** (31 Jan + 2 months = 31 Mar; 31 Jan + 1 month = 28 Feb, or 29 in a leap year). Everything uses the local clock of the machine running the server.

## The server

`server.py` is about 150 lines on top of `http.server`:

- **Binding:** `127.0.0.1:8000` (edit `HOST`/`PORT` at the top of the file).
- **Routes:** `GET /` and `/index.html`, `GET /health`, `GET /docs/img/icon.png`, `POST /chat`, plus `OPTIONS` for CORS preflight. Everything else is `404`. The static-file table (`STATIC_FILES`) is a whitelist, so source code, the brain and other images cannot be downloaded.
- **Limits and validation:** bodies over 64 KiB → `413`; a negative or invalid `Content-Length`, invalid JSON, a non-object body or a non-string `message` → `400`.
- **CORS:** `Access-Control-Allow-Origin: *`, which lets the page work when opened straight from disk (`file://`). Because the server only listens on localhost, other computers cannot reach it.
- **Error handling:** if the engine ever raises, the server still answers `200` with `skill: "error"` and a readable message instead of dropping the connection.
- **Startup:** the engine is built before the server starts, so a broken `brain.json` fails immediately with a clear error.

## The frontend

`src/index.html` is one file: markup, CSS and JavaScript.

- Sends messages to `/chat` (same origin), or to `http://localhost:8000/chat` when the page is opened from disk.
- **Safe rendering:** reply text is HTML-escaped first; only `**bold**`, `` `code` `` and line breaks are turned into markup.
- **Chips:** `suggestions` from the reply become buttons; clicking one sends its label.
- **UX details:** typing indicator, timestamps, auto-scroll, input and button disabled while waiting, a 500-character input limit, a clear button that restarts the conversation with a greeting, and a helpful error bubble if the server cannot be reached.
- **Images:** Nova's avatar is `../docs/img/icon.png` (relative to `src/`), which resolves correctly both from disk and when served at `/`. The user's avatar is an inline SVG.

## Design decisions

- **Skills before the brain.** Exact answers must never be replaced by a lookalike chat reply.
- **JSON for personality.** Anyone can add a reply or a typo fix without touching Python.
- **No `eval()`, ever.** User text is only ever parsed into a syntax tree and checked node by node.
- **Standard library only.** Nothing to install, nothing to break, nothing that phones home.
- **Localhost only.** The server is a personal tool; it is not hardened for the public internet and must not be exposed to it.
- **Deliberately small.** Each file can be read in a few minutes, which keeps Nova useful as a learning project.

## The Java implementation

Status: **a partial port, not an alternative runtime.**

- It implements the **math and time skills** with the same detection rules and wording as Python, and a small command-line demo.
- It has **no HTTP server and does not read `brain.json`**, so it cannot hold a conversation.
- It compiles and runs on OpenJDK 21; Java 17 as a target was not verified locally.
- Python and Java agree on the same inputs except where Java's `double` arithmetic differs from Python's exact integers (whole results above 2^53, such as `9^64`) and possibly in the formatting of very small or very large non-integer results.

## Tests

`tests/test_nova.py` (28 tests, standard library only) covers: the brain file's structure; math answers and refusals; time answers and a list of phrases that must **not** trigger it; engine routing, typo and slang handling, fallbacks and word-boundary matching; and the HTTP server (health, page, icon, chat, bad requests, oversized bodies, nothing else served). Run from the repository root:

```bash
python -m unittest discover -s tests -v
```

## Current limitations

No conversation memory, English-only matching, a small content set, no time zones, single user, no live data. Details: [is Nova any good?](../help/is-nova-good.md).

## Extending Nova

- Add replies or fix typos: [the JSON brain](../help/the-json-brain.md).
- Add an exact-answer skill: [create your own skill](../help/_create-skill/create-your-own-skill.md).
- Run Nova on a phone or another OS: [platform compatibility](compatible/android-comp.md).
