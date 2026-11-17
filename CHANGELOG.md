# Changelog

All notable changes to Nova are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0] - 2026-11-17

First release.

### Added
- Chat page (`src/index.html`) with typing indicator, quick-reply chips and a responsive layout.
- Python engine (`src/py/`) that routes each message through a math skill, a time and date skill, the JSON brain and a fallback reply.
- JSON brain (`src/json/brain.json`): 62 topics, 428 patterns, 211 replies, 61 phrase fixes and 127 typo fixes.
- HTTP server (`server.py`) with `POST /chat`, `GET /health`, input validation and a static-file whitelist.
- Java port of the math and time skills with a command-line demo (`src/java/`).
- MIT license.
- 28 automated tests, guides under `help/` and documentation under `docs/`, with README translations in four languages.
