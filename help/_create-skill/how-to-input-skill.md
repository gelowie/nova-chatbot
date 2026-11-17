# What a skill receives and returns

## Input

Each skill is called as `handle(message)` with one argument:

- `message` is a `str`: the user's text with leading and trailing whitespace removed. It is **not** lowercased or otherwise normalized, so do that yourself (`message.lower()`), and match with regular expressions using word boundaries (`\b`) so that, for example, "update" does not match "date".
- It is never empty; empty messages are answered with a fallback before any skill runs.
- The browser page limits messages to 500 characters, but `POST /chat` accepts up to 64 KiB, so do not assume short input.
- A skill receives only the current message. Nova keeps no conversation history.

## Output

Return either:

- a **non-empty `str`** – it becomes the reply and no further layer is tried, or
- **`None`** – "not for me"; the next skill, and then the JSON brain, get their turn.

Do not return an empty string (it is treated as "no answer") and do not raise exceptions for ordinary input. Catch errors you can anticipate and return a friendly sentence or `None`.

## Formatting the reply

The chat page renders `**bold**`, `` `code` `` and line breaks (`\n`); all other characters are shown as plain text. Keep replies short.

## Quick replies

Skill replies get the engine's default suggestion chips (`"Tell me a joke"`, `"What can you do?"`, `"What time is it?"`). Skills cannot choose their own chips today.

## Checking your input assumptions

Try awkward input before you commit: mixed case, extra spaces, very long numbers, messages that contain your trigger word in ordinary chat. The test suite in `tests/test_nova.py` has examples (`MUST_ANSWER` / `MUST_IGNORE` in the time tests).
