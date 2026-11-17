# Installing Nova

Nova has no third-party dependencies, so "installing" means getting the files and running one command.

## Requirements

| | Needed for | Version |
|---|---|---|
| Python | Running Nova (server, engine, tests) | 3.10 or newer (developed and tested with 3.12) |
| A web browser | Using the chat page | Any current browser |
| JDK (optional) | The Java skills demo only | 17 or newer recommended (tested with OpenJDK 21; the code uses records, which need 16+) |

No internet connection is needed after you have the files. Disk space: well under 1 MB.

Platform-specific notes: [Android / Termux](../docs/compatible/android-comp.md) · [Windows](../docs/compatible/windows-comp.md) · [Linux and macOS](../docs/compatible/linux-macos-comp.md).

## 1. Get the project

```bash
git clone https://github.com/gelowie/nova-chatbot.git
cd nova-chatbot
```

Or download the repository as a ZIP from GitHub, unzip it, and open a terminal in the folder that contains `server.py`. If the folder name contains spaces or parentheses (for example `nova-chatbot-github (fix it)`), put it in quotes when you `cd` into it.

## 2. Check Python

```bash
python --version      # on macOS/Linux/Termux you may need: python3 --version
```

It must print 3.10 or higher.

## 3. Start Nova

```bash
python server.py      # on macOS/Linux/Termux you may need: python3 server.py
```

You should see:

```
🟢 Nova engine listening on http://127.0.0.1:8000
   Open http://127.0.0.1:8000 in your browser, or POST to /chat
   Brain loaded from: .../src/json/brain.json
   Frontend file:     .../src/index.html
   Press Ctrl+C to stop.
```

Open <http://127.0.0.1:8000> in your browser and start chatting. Stop the server with `Ctrl+C`.

You can start `server.py` from any folder (for example `python path/to/nova-chatbot/server.py`); it finds its own files. The tests, however, should be run from the repository root.

## 4. Check that it works

With the server running, in another terminal:

```bash
curl http://127.0.0.1:8000/health
# {"ok":true}

curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"message": "whats 5 plus 3 times 2"}'
```

Or run the automated tests (the server does not need to be running):

```bash
python -m unittest discover -s tests -v
```

All 28 tests should pass.

## Changing the port or address

Near the top of `server.py`:

```python
HOST = "127.0.0.1"
PORT = 8000
```

Keep `HOST` as `127.0.0.1` unless you understand the consequences: Nova has no login, so anyone who can reach the port can chat with it.

## Optional: the Java skills demo

```bash
javac -encoding UTF-8 -d out src/java/*.java
java -cp out nova.NovaEngine
```

If accented or special characters print as `?`, your terminal is not using UTF-8: run `java -Dstdout.encoding=UTF-8 -cp out nova.NovaEngine` (Java 19+), or switch the terminal to UTF-8 (on Windows: `chcp 65001`). The Java code covers the math and time skills only; see [the architecture](../docs/nova.md#the-java-implementation).

## Troubleshooting

| Problem | Fix |
|---|---|
| `python: command not found` | Try `python3` (or `py -3` on Windows), or install Python from <https://www.python.org/downloads/>. |
| `ModuleNotFoundError: No module named 'src'` | You are running a copy of the code without the `src/` folder, or running the tests from the wrong folder. Run from the repository root. |
| `FileNotFoundError` mentioning `brain.json` | `src/json/brain.json` is missing; restore it from a full checkout. |
| `Address already in use` | Another program uses port 8000. Stop it, or change `PORT` near the top of `server.py`. |
| The chat page says it could not get a reply | The server is not running. Start it with `python server.py` in another terminal. |
| Startup fails with a JSON error | `src/json/brain.json` has a syntax error (usually a missing comma or quote). The error message names the line. |
| The page loads but the avatar image is missing | Start the server from a full checkout; the page needs `docs/img/icon.png`. |
| `UnicodeEncodeError` when starting on Windows | Run `set PYTHONUTF8=1` (Command Prompt) or `$env:PYTHONUTF8=1` (PowerShell) first. |
