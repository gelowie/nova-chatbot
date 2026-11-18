# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 1.x | Yes |

## Reporting a vulnerability

Please do not open a public issue. Report it privately through the [security advisory form](https://github.com/gelowie/nova-chatbot/security/advisories/new) and include:

- What you found and where (file, route or message).
- Steps or an example request that reproduces it.
- The Nova version, Python version and operating system.

Reports are handled on a best-effort basis. You will get a reply in the advisory thread, and a fix is credited to you unless you prefer otherwise.

## What counts as a vulnerability

Nova runs locally and has no accounts, but these would all be treated as security bugs:

- Reading a file through the server that is not on the static whitelist (`STATIC_FILES` in `server.py`), such as the source code or `brain.json`.
- Running code through the math skill. Input is parsed into a syntax tree and only numbers and whitelisted operators are evaluated; `eval()` is never used.
- Input that makes the server crash, hang or use unbounded memory (the 64 KiB request limit and the exponent cap exist for this).
- Script injection in the chat page. Reply text is HTML-escaped before the few supported formatting markers are applied.
- Any outgoing network request, or any data written to disk, which Nova must never do.

## Out of scope

- Exposing the server to a network or the internet by changing `HOST` in `server.py`. Nova has no login by design and is meant to listen on `127.0.0.1` only.
- Attacks that need control of the machine running Nova.
- The content of brain replies, unless it is harmful. Report that as a normal issue.
