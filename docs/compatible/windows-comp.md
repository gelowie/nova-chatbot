# Nova on Windows

**Short answer:** yes. Nova is plain Python with no dependencies, so it runs on Windows 10 and 11 wherever Python 3.10+ is installed.

> **Verification status:** Nova was run and tested on Linux (Python 3.12). It uses only cross-platform standard-library code (`pathlib`, `http.server`), so it is expected to work on Windows as described here, but these steps have not been verified on a Windows machine. If something differs for you, please open an issue.

## What you need

| | |
|---|---|
| Windows | 10 or 11 |
| Python | 3.10 or newer from <https://www.python.org/downloads/> (tick **Add python.exe to PATH** in the installer) or from the Microsoft Store |
| Browser | Any current browser |
| JDK (optional) | 17 or newer, only for the Java demo |

## Install and run

Open **PowerShell**, **Command Prompt** or **Windows Terminal** in the folder you want to use:

```powershell
git clone https://github.com/gelowie/nova-chatbot.git
cd nova-chatbot
python server.py
```

No Git? Download the ZIP from GitHub, extract it, and open a terminal in the folder that contains `server.py` (in File Explorer, click the address bar, type `cmd` and press Enter).

Then open **<http://127.0.0.1:8000>** in your browser. Stop the server with `Ctrl+C`.

If `python` is not recognized, try the Python launcher instead: `py -3 server.py`.

If your folder path contains spaces or parentheses, put it in quotes when you `cd`: `cd "C:\Users\you\nova chatbot (copy)"`.

## Windows Firewall

Nova listens on `127.0.0.1` only, so Windows Firewall normally does not ask about it. If a prompt does appear, you can choose *Cancel* / *Block*; Nova does not need network access.

## Emoji and special characters

Nova prints a few emoji (such as 🟢) when it starts. Modern terminals (Windows Terminal, current PowerShell and Command Prompt) display them. If output is redirected to a file or an older console shows an encoding error, switch Python to UTF-8 mode before starting:

```powershell
# PowerShell
$env:PYTHONUTF8 = "1"
python server.py
```

```bat
:: Command Prompt
set PYTHONUTF8=1
python server.py
```

The chat page itself is not affected; it always uses UTF-8.

## Talking to the API from the command line

In PowerShell, `curl` is an alias for another command, so use `curl.exe` or `Invoke-RestMethod`:

```powershell
curl.exe http://127.0.0.1:8000/health

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/chat `
  -ContentType "application/json" `
  -Body '{"message": "whats 5 plus 3 times 2"}'
```

## The Java demo (optional)

```powershell
javac -encoding UTF-8 -d out src\java\*.java
java -Dstdout.encoding=UTF-8 -cp out nova.NovaEngine
```

If special characters print as `?`, run `chcp 65001` first.

## Run the tests

```powershell
python -m unittest discover -s tests -v
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` opens the Microsoft Store | Install Python from python.org, or turn off the *App execution aliases* for Python in Windows settings. |
| `'python' is not recognized` | Reinstall Python with *Add python.exe to PATH* ticked, or use `py -3`. |
| `Address already in use` / `Only one usage of each socket address` | Another program uses port 8000. Stop it or change `PORT` in `server.py`. |
| `UnicodeEncodeError` at startup | Set `PYTHONUTF8=1` as shown above. |
| The page loads but the avatar is missing | Start the server from the repository's root folder so `docs\img\icon.png` exists. |

## Windows Subsystem for Linux

If you use WSL, follow the [Linux and macOS](linux-macos-comp.md) instructions inside your WSL terminal. Open <http://127.0.0.1:8000> in the Windows browser; WSL forwards localhost.
