# Nova on Android (and other phones)

**Short answer:** yes. Nova is not an Android app (there is no APK), but it is plain Python with no dependencies, so it runs on Android inside **Termux**, a terminal app with a real Python. You then chat with it in the phone's browser.

> **Verification status:** Nova was run and tested on Linux (Python 3.12). Termux is a Linux-like environment with the same Python, and Nova uses only the standard library, so it is expected to work as described here, but these steps have not been verified on a physical Android device. If something differs on your phone, please open an issue.

## What you need

| | |
|---|---|
| Android | A version supported by current Termux |
| Termux | Install it from **F-Droid** or the Termux GitHub releases, as the Termux project recommends. Older Google Play builds are outdated and their package repositories may not work. |
| Python | 3.10 or newer (installed with `pkg`, see below) |
| Browser | Any phone browser |
| Storage | A few MB; the project is under 1 MB |

## Install and run

Open Termux and run:

```bash
pkg update && pkg upgrade
pkg install python git
git clone https://github.com/gelowie/nova-chatbot.git
cd nova-chatbot
python server.py
```

Then open **<http://127.0.0.1:8000>** (or `http://localhost:8000`) in the phone's browser. Keep Termux running in the background while you chat. Stop Nova with `Ctrl+C` (the volume-down key acts as `Ctrl` in Termux's extra keys row).

### If you have Nova as a ZIP file

```bash
termux-setup-storage            # once; grants access to your phone's storage
pkg install unzip
cp ~/storage/downloads/nova-chatbot.zip ~
unzip nova-chatbot.zip
cd nova-chatbot                 # use the real folder name; quote it if it has spaces
python server.py
```

Run Nova from Termux's own home folder (`~`) rather than directly from shared storage (`/sdcard`); it is faster and avoids permission surprises.

## Keeping it alive

Android may stop background apps to save battery. If Nova stops answering while Termux is in the background:

- Run `termux-wake-lock` in Termux (or tap *Acquire wakelock* in Termux's notification).
- Exclude Termux from battery optimization in Android's settings.

## Time and date

The time skill reads the clock and time zone that Python sees. If Nova's time is off by your UTC offset, set the zone before starting:

```bash
export TZ=Region/City      # for example: export TZ=Europe/Paris
python server.py
```

## Using it from another device on the same Wi-Fi (optional, read the warning)

By default Nova listens on `127.0.0.1`, which only the phone itself can reach. To open it from a laptop on the same network you would change `HOST = "127.0.0.1"` to `HOST = "0.0.0.0"` in `server.py`.

> **Warning:** Nova has no login, and it answers requests from any web page. Anyone on that network could then talk to it. Only do this on a network you trust, and change it back afterwards. Nova is a personal tool and is not designed to be exposed to the internet.

## The Java demo (optional)

```bash
pkg install openjdk-17            # or a newer openjdk package
javac -encoding UTF-8 -d out src/java/*.java
java -cp out nova.NovaEngine
```

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `python: command not found` | `pkg install python` |
| `git: command not found` | `pkg install git` |
| `Address already in use` | Another process uses port 8000. Close it, or change `PORT` in `server.py`. |
| The browser says it cannot connect | Make sure `python server.py` is still running in Termux, and use `http://127.0.0.1:8000`. |
| Nova stops after a while | See *Keeping it alive* above. |
| The chat works but the avatar is missing | Start the server from the repository's root folder so `docs/img/icon.png` exists. |

## iPhone and iPad

iOS has no official terminal, so Nova cannot be installed there directly. Apps that provide a Python environment (for example a-Shell or iSH) might run it, but this has not been tested. The reliable option is to run Nova on a computer or an Android device and, on a network you trust, open it from the iPhone's browser as described above.
