# Nova on Linux and macOS

**Short answer:** yes. This is the platform Nova was developed and tested on.

> **Verification status:** the full test suite (28 tests) and the Java demo were run on Linux (Ubuntu, Python 3.12, OpenJDK 21) while preparing this documentation. macOS uses the same Python code and is expected to behave identically but was not run here.

## What you need

| | |
|---|---|
| Python | 3.10 or newer (3.12 recommended) |
| Browser | Any current browser |
| JDK (optional) | 17 or newer, only for the Java demo |

Check your version:

```bash
python3 --version
```

Install Python if needed:

| System | Command |
|---|---|
| Debian / Ubuntu | `sudo apt install python3` |
| Fedora | `sudo dnf install python3` |
| Arch | `sudo pacman -S python` |
| macOS | `brew install python` (Homebrew), or the installer from <https://www.python.org/downloads/> |

## Install and run

```bash
git clone https://github.com/gelowie/nova-chatbot.git
cd nova-chatbot
python3 server.py
```

Open **<http://127.0.0.1:8000>** and stop the server with `Ctrl+C`. Check it from another terminal:

```bash
curl http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"message": "what day is it"}'
```

## Run it in the background (optional)

```bash
nohup python3 server.py > nova.log 2>&1 &     # start; output goes to nova.log (ignored by git)
kill %1                                         # stop it again, from the same shell
```

For a long-running setup, a `systemd --user` service or `tmux` session works equally well. Remember that Nova is a personal tool: keep it bound to `127.0.0.1` and do not expose it to the internet.

## The Java demo (optional)

```bash
# Debian/Ubuntu: sudo apt install default-jdk      macOS: brew install openjdk
javac -encoding UTF-8 -d out src/java/*.java
java -cp out nova.NovaEngine
```

If special characters print as `?`, run `java -Dstdout.encoding=UTF-8 -cp out nova.NovaEngine` (Java 19+) or make sure your terminal uses UTF-8. The `out/` folder is ignored by git.

## Run the tests

```bash
python3 -m unittest discover -s tests -v
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `python: command not found` | Use `python3`. |
| `Address already in use` | Find the process with `lsof -i :8000` (macOS/Linux) or `ss -ltnp \| grep 8000` (Linux), stop it, or change `PORT` in `server.py`. |
| Unexpected errors on start | Check that `python3 --version` is 3.10 or newer; older versions are not supported or tested. |
| The time is wrong | Nova uses the system clock and time zone. Fix the system settings, or set `TZ` (for example `TZ=Europe/Paris python3 server.py`). |
| The page loads but the avatar is missing | Start the server from a full checkout so `docs/img/icon.png` exists. |
