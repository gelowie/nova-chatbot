# The JSON brain

`src/json/brain.json` holds everything Nova *says* in conversation. The Python engine loads it once at startup (**restart the server after editing it**).

## Contents

- [Structure](#structure)
- [An intent in detail](#an-intent-in-detail)
- [How a message is matched](#how-a-message-is-matched)
- [The topics in the brain](#the-topics-in-the-brain)
- [Adding or changing things](#adding-or-changing-things)
- [Writing good patterns and replies](#writing-good-patterns-and-replies)
- [Checking your changes](#checking-your-changes)
- [Known quirks](#known-quirks)

## Structure

| Key | Type | Used by the engine? | Purpose |
|---|---|---|---|
| `meta` | object | yes | `name`, `version` (version of the brain data, not a software release), `fallbacks` (5 replies when nothing matches) and `unknownSuggestions` (the chips shown with a fallback). |
| `phraseFixes` | object | yes | Slang and abbreviations expanded before matching (`"hru"` → `"how are you"`). 61 entries. |
| `typos` | object | yes | Misspellings corrected before matching (`"helo"` → `"hello"`). 127 entries. |
| `intents` | array | yes | The conversation topics (62 intents, 428 patterns, 211 replies). |
| `synonyms` | object | **no** | Present in the file (12 word groups) but not read by the current engine. |

The numbers quoted in these docs (62 intents, 428 patterns, 211 replies, 61 phrase fixes, 127 typo fixes) were counted from the file; update the docs if you change them substantially.

## An intent in detail

```json
{
  "tag": "greeting",
  "priority": 1,
  "patterns": ["hello", "hi there", "hey nova"],
  "keywords": ["hello", "hi", "hey"],
  "responses": ["Hello! 😊 Great to see you. How can I help?"],
  "suggestions": ["What can you do?", "Tell me a joke"]
}
```

| Field | Used? | Meaning |
|---|---|---|
| `tag` | yes | Unique name of the intent (lowercase, snake_case). Used to avoid repeating the same reply twice in a row. |
| `priority` | yes | Multiplier applied to the match score. `1` is normal; a higher number makes the intent win close calls (`capabilities` uses `1.1`, `joke` `1.15`). Optional, defaults to `1`. |
| `patterns` | yes | Example messages that should trigger this intent. |
| `responses` | yes | Possible replies; one is chosen at random, never the same one twice in a row. May use `**bold**`, `` `code` `` and `\n` for line breaks. |
| `suggestions` | yes | Quick-reply chips shown after the reply. Falls back to a default set of three chips. Eight intents define their own. |
| `keywords` | **no** | Stored on every intent but not read by the current engine. |

Reply text is shown by the chat page after HTML-escaping, so you cannot inject markup; only `**bold**`, `` `code` `` and line breaks are rendered.

## How a message is matched

1. **Normalize.** Lowercase; every character other than `a-z`, `0-9`, `'` and spaces becomes a space (so matching is English-only); then the entries of `phraseFixes` and `typos` are applied as whole words, longest first.
2. **Score every pattern.** Score = token overlap (shared words ÷ all distinct words in both texts). If the normalized pattern appears in the message as whole words, the overlap is raised to at least **0.95**. The pattern's last letter may be stretched, so `heyyy` and `helloooo` still contain `hey` and `hello`, but `this` does not contain `hi`, `you` does not contain `yo`, and `helped` does not contain `help`. The result is multiplied by the intent's `priority`.
3. **Pick the best.** The highest score wins if it is at least **0.35**; otherwise Nova uses a fallback reply. When two patterns tie, the one that appears first in the file wins.
4. **Choose a reply.** A random entry from `responses`, different from the previous one given for that intent.

Math and time skills are tried **before** the brain. The brain's `time` and `date` intents therefore only answer if the time skill declines a message.

A worked example for `i am really tired` (real scores from the engine):

| Pattern (intent) | Shared words ÷ all distinct words | Contained as whole words? | Score |
|---|---|---|---|
| `i am tired` (`tired`) | 3 ÷ 4 = 0.75 | no | **0.75** |
| `i am so tired` (`tired`) | 3 ÷ 5 = 0.60 | no | 0.60 |
| `i am leaving` (`goodbye`), `i am sorry` (`sorry`), `i am hungry` (`food`) | 2 ÷ 5 = 0.40 | no | 0.40 |

The best score is 0.75 (at least 0.35), so Nova answers from the `tired` intent. If the message had been exactly `i am tired`, the pattern would also be contained in the message and the score would be 1.0.

## The topics in the brain

| Group | Intent tags |
|---|---|
| Conversation basics (19) | `greeting`, `how_are_you`, `bot_feeling`, `bot_name`, `bot_creator`, `bot_age`, `bot_identity`, `capabilities`, `thanks`, `goodbye`, `sorry`, `compliment`, `compliment_back`, `insult`, `love`, `yes`, `no`, `secret`, `contact` |
| Everyday questions (7) | `time`, `date`, `weather`, `math_help`, `news`, `location`, `language` |
| Entertainment (13) | `joke` (10 replies), `fact` (7), `quote` (5), `riddle` (4), `music`, `movie`, `sport`, `hobby`, `games`, `books`, `sing`, `dance`, `color` |
| Food and animals (6) | `food`, `pizza`, `coffee`, `animals`, `dogs`, `cats` |
| Feelings and wellbeing (8) | `sad`, `happy`, `bored`, `tired`, `sleep`, `health`, `motivation`, `meaning_of_life` |
| Advice and learning (9) | `study`, `work`, `coding`, `javascript`, `python`, `ai`, `money`, `travel`, `advice` |

## Adding or changing things

**A new intent:** append an object to `intents` with a unique `tag`, several `patterns` (include the different ways people phrase it), and at least one `response`. Restart the server and try it. Example:

```json
{
  "tag": "weekend",
  "patterns": ["weekend plans", "what should i do this weekend", "it is the weekend"],
  "responses": ["Weekend mode: ON. 🛋️ Rest first, then something small and fun."],
  "suggestions": ["Tell me a joke", "Fun fact"]
}
```

**A new reply for an existing topic:** add a string to that intent's `responses`.

**A new typo or slang fix:** add `"yall": "you all"` to `phraseFixes` (or `typos`). Keys should be lowercase and use only letters, digits and apostrophes. Fixes apply to whole words only.

**Make one intent win more often:** raise its `priority` slightly (for example `1.05`). Large values make it swallow unrelated messages, so change it carefully.

**Change the fallback messages:** edit `meta.fallbacks` and `meta.unknownSuggestions`.

## Writing good patterns and replies

- Write patterns the way people actually type: short, lowercase, without punctuation. Punctuation is removed anyway.
- Add several phrasings per intent; a pattern is matched either as a whole phrase or by overlapping words.
- **Prefer patterns of two words or more.** A single common word as a pattern will match every message that contains it as a whole word, so give such words a specific intent only if you really want that.
- Avoid putting the same pattern in two intents; the first one in the file will win.
- Keep the same tone across replies of one intent, and write at least three replies so the "no repeat" logic has something to choose from.
- Do not leave placeholder replies such as `"Here is what I do: ..."`. The test suite rejects replies that end with `: ...`.
- Use `suggestions` to guide the next message; make them phrases that the brain or a skill really understands.

## Checking your changes

```bash
python -m unittest discover -s tests -v
```

The tests check that the file is valid JSON, tags are unique, every pattern and response is non-empty text, no reply is an unfinished placeholder, and every brain pattern is answered by the brain rather than swallowed by a skill (except the `time`, `date` and `math_help` intents, which skills are meant to handle).

Quick manual check without starting the server:

```bash
python -c "from src.py import NovaEngine; print(NovaEngine('src/json/brain.json').respond('your test message'))"
```

## Known quirks

- **A broad, high-priority pattern can outrank a specific one.** `capabilities` has priority `1.1` and the pattern `help me`, so `help me study` and `help me with math` are answered with Nova's help text instead of the `study` or `math_help` intents. If this bothers you, lower the priority of `capabilities`, or add longer patterns (`help me study for an exam`) to the specific intents.
- **Ties go to the first intent in the file.** `python vs javascript` (a `python` pattern) and `javascript vs python` (a `javascript` pattern) use the same words, so they tie exactly and both are answered by `javascript`, which comes first.
- **No stemming.** `studying` does not match `study`; add both forms (or a typo fix) if you want both.
- **Short messages match loosely.** With few words, one shared word gives a high overlap, so a brief message such as `what is this` ties at 0.5 with `what is up`, `what is today`, `what is python` and others, and the first of them in the file (the greeting) answers.
- **`keywords` and `synonyms` are ignored** by the current engine. They are kept as data for a future matcher.
