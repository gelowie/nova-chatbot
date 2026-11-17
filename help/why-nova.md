# Why Nova exists

Nova is a project that shows you do not need a cloud service to build a friendly, useful chat assistant. Everything that makes it work is in this repository and can be read in an afternoon:

- the **personality** (replies, jokes, advice) is plain JSON,
- the **logic** (routing, math, dates) is short Python,
- the **interface** is a single HTML file.

## What it is useful for

- **A learning project.** See how a rule-based chatbot works under the hood: normalizing text, fixing typos, scoring matches, choosing replies, and wrapping it all in a small web server. Every step is a few lines of readable code.
- **A template.** Edit the JSON brain to give your own assistant a different personality, or add a skill (see [creating a skill](_create-skill/create-your-own-skill.md)) for anything that needs an exact answer.
- **A demonstration of "JSON as a brain"** combined with ordinary code for the parts that need exact answers (math and dates). Knowing *when not to use fuzzy matching* is the main lesson of the project.
- **A private chat companion.** The server listens only on your own machine (`127.0.0.1`) and your messages are never sent anywhere.
- **A base for experiments.** Because the engine is deterministic, you can write tests for it, something that is hard to do when replies are generated freely.

## The ideas behind it

1. **Exact where it matters.** Arithmetic and dates are computed by code. A chatbot that guesses `5 + 3 × 2` is worse than a calculator.
2. **Editable by anyone.** Adding a joke should never require changing a program.
3. **Transparent.** If Nova says something odd, you can open the JSON or the Python and find out exactly why.
4. **Safe by construction.** No `eval()`, no outside calls, no accounts, nothing stored.
5. **Small enough to finish.** A project you can read completely is a project you can trust and extend.

If you need open-ended answers, long-term memory or live information, Nova is the wrong tool. See [is Nova any good?](is-nova-good.md) for an honest comparison of strengths and limits.
