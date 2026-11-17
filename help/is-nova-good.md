# Is Nova any good?

That depends on what you want. This page is an honest summary of what Nova does well, where it stops, and the known quirks you may run into.

## What it does well

- **Exact math and date answers.** Arithmetic is evaluated by code, not guessed. The math skill walks a restricted syntax tree and never calls `eval()`, so a message cannot run arbitrary code.
- **Predictable and inspectable.** Every reply comes from `brain.json` or a few hundred lines of Python. If Nova says something odd, you can find out why.
- **Tolerant of messy typing.** Phrase fixes (61) and typo fixes (127) are applied before matching, and the matcher scores word overlap rather than requiring exact text, so "helo", "wat r u doin" and "helloooo thereeee" still find the right answer.
- **Fast and light.** Matching takes well under a millisecond per message on a normal computer. There is nothing to download and nothing to install.
- **Private.** No network calls; the server binds to `127.0.0.1`.
- **Easy to extend.** New replies are JSON edits; new exact-answer skills are one small Python file.
- **Tested.** 28 automated tests, including lists of phrases that must *not* trigger a skill.

## Where it stops

- **Rule-based.** It matches patterns. Questions outside the brain's 62 topics get a fallback reply.
- **No memory.** Each message is handled independently, so "and what about tomorrow?" means nothing to it.
- **Small content.** For example the brain holds 10 jokes, 7 facts, 5 quotes and 4 riddles.
- **English only for matching.** Text is reduced to the letters a-z, digits and apostrophes before matching, so other alphabets and accented letters do not match brain patterns.
- **Date and time are a best effort.** The skills read your computer's clock and calendar. They have no concept of time zones or places.
- **Single user.** The server is meant for one person on one machine, and its "don't repeat the last reply" memory is shared by everyone who uses it.

## Known quirks

These are real behaviours, listed so they do not surprise you. Most can be changed if they bother you.

| Quirk | Example | Why |
|---|---|---|
| The words `date` or `clock` anywhere in a message trigger the time skill. | `i have a date tonight` answers with today's date. | The date rule is deliberately broad so that "what is the date" always works. |
| Time zones are not understood. | `what time is it in tokyo` gives your local time. | The skill only reads the local clock. |
| Exponents above 64 are refused. | `2 ** 100` gets a fallback reply (`2 ** 64` works). | Protection against memory-exhausting expressions. |
| Floor division is echoed oddly. | `7 // 2` is solved correctly (3) but shown as `7 ÷ ÷ 2`. | Cosmetic: the display step does not know about `//`. |
| A short, generic, high-priority pattern can outrank a specific one. | `help me study` answers with Nova's help text, not study advice. | `capabilities` has priority 1.1 and a pattern `help me`. See [the JSON brain](the-json-brain.md#known-quirks). |
| Random replies may include playful or off-topic lines. | Asking for help sometimes gets a joke. | Replies are picked at random from everything listed for the intent, including playful extras. |

## Who should use it

People who want to learn from a small, readable chatbot, or who want a base to extend with their own skills and replies. Not people who want a general-purpose assistant.
