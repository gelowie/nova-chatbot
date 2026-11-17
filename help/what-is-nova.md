# What is Nova?

Nova is a small **chatbot that runs entirely on your own computer**. It needs no internet connection, no account, no API key and no `pip install`; it uses only the Python standard library. You start one script, open a web page on your own machine, and chat.

## In one minute

- You type a message in a browser chat window.
- A tiny local server hands it to Nova's engine.
- The engine tries to answer in **three layers**, in this order, and the first layer that has an answer wins:

1. **Math skill** (`src/py/math_solver.py`) – evaluates arithmetic such as "whats 5 plus 3 times 2" or "15% of 200". The answer is computed, never guessed.
2. **Time skill** (`src/py/time_reader.py`) – answers questions about the current time, today's date, the weekday, tomorrow/yesterday, next/last month and simple date shifts such as "in 3 weeks".
3. **JSON brain** (`src/json/brain.json`) – a hand-written knowledge base of 62 conversation topics (greetings, small talk, jokes, advice, recommendations and more) matched with typo-tolerant fuzzy matching.

If none of them understands the message, Nova replies with a friendly "I didn't catch that" message and some suggestions to try.

## What Nova can do

| Area | Examples | Handled by |
|---|---|---|
| Arithmetic | `24 * 7 + 3`, `144 divided by 12`, `15% of 200`, `2^10`, `3 squared plus 4 squared` | math skill |
| Clock and calendar | `what time is it`, `what day is it`, `what is tomorrow`, `date next month`, `in 3 weeks` | time skill |
| Small talk | `hello`, `how are you`, `who are you`, `thanks`, `bye` | JSON brain |
| Feelings and support | `i am sad`, `i am bored`, `i am tired`, `i need motivation` | JSON brain |
| Entertainment | `tell me a joke`, `fun fact`, `give me a quote`, `riddle` | JSON brain |
| Advice and tips | study, work, money, health, travel, coding, Python, JavaScript | JSON brain |
| Recommendations | music, movies, books, games, food, sports | JSON brain |
| Messy typing | `helo`, `hru`, `wat r u doin`, `helloooo thereeee`, `thx` | typo and slang fixes |

## What Nova is not

Nova has no language model and no memory of earlier messages: each message is answered on its own. It cannot browse the internet, fetch live data such as the weather, understand time zones, or read files and images. Its replies are the ones written in `brain.json` and the answers computed by the two skills. That is not a flaw to hide; it is what makes Nova small, fast, private and fully understandable.

## The parts of the project

| Part | Where | What it does |
|---|---|---|
| Python engine | `src/py/` | Routes each message to a skill or to the brain. This is the supported implementation. |
| JSON brain | `src/json/brain.json` | Replies, matching patterns, typo and slang fixes. |
| Server | `server.py` | A small standard-library HTTP server: serves the chat page and answers `POST /chat`. |
| Frontend | `src/index.html` | The browser chat window (one HTML file with its CSS and JavaScript). |
| Java implementation | `src/java/` | A Java version of the math and time skills with a command-line demo. It has no server and does not read the JSON brain. |
| Tests | `tests/test_nova.py` | Automated checks for everything above. |
| Documentation | `docs/`, `help/` | Architecture, platform notes, translations and these guides. |

## Where to go next

- Run it: [installing Nova](installing-nova.md), then [how to use Nova](how-to-use-nova.md).
- Understand it: [architecture](../docs/nova.md).
- Change it: [the JSON brain](the-json-brain.md) and [create your own skill](_create-skill/create-your-own-skill.md).
- Judge it: [is Nova any good?](is-nova-good.md)
