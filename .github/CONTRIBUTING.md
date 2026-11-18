# Contributing to Nova

Thanks for your interest in Nova. Bug reports, brain additions, new skills and documentation fixes are all welcome. By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Before you start

* Check the [open issues](https://github.com/gelowie/nova-chatbot/issues) in case your idea or bug is already there.
* For anything larger than a small fix, open an issue first so the approach can be agreed before you write code.
* Keep Nova's core idea intact: it runs locally, has no third-party dependencies and makes no outgoing network calls. Changes that add a dependency or a network request will not be accepted.

## Setup

You need Python 3.10 or newer. A JDK (17 or newer) is needed only if you touch the Java files.

```bash
git clone https://github.com/gelowie/nova-chatbot.git
cd nova-chatbot
python server.py        # on macOS, Linux and Termux you may need: python3 server.py
```

Run `server.py` and the tests from the repository root, because the engine is imported as `from src.py import NovaEngine`.

## Ways to contribute

### Improve the brain

Most contributions are edits to [`src/json/brain.json`](../src/json/brain.json): new topics, more patterns or replies, and typo or slang fixes. If you would rather suggest than edit, use the **Brain suggestion** issue form. Read [the JSON brain](../help/the-json-brain.md) first. In short:

* Keep the file valid JSON and every reply complete (the tests check for unfinished replies).
* Write patterns in lowercase English without punctuation.
* Give a topic several replies where it makes sense; Nova never repeats the same one twice in a row.
* Use `priority` sparingly. A high-priority broad pattern can outrank a more specific one.
* Restart the server to load your changes.

### Add or change a skill

Skills are small Python modules that return an exact answer or `None`. Follow [create your own skill](../help/_create-skill/create-your-own-skill.md). If you change the math or time skill, update the matching file in [`src/java/`](../src/java/) so the two stay consistent.

### Fix bugs and improve the docs

Documentation lives in the README, [`docs/`](../docs/) and [`help/`](../help/). If you change user-facing behaviour, update the docs that describe it. The translated READMEs in [`docs/readme/`](../docs/readme/) follow the English README; if you can't update them, say so in your pull request and a maintainer will follow up.

## Code style

* Follow the conventions already in the file you are editing. Prefer clear, conventional code over clever code.
* Python: standard library only, early returns instead of deep nesting, specific exception types, and no silently swallowed errors.
* Use domain-specific names. Comments explain why something is done, not what the code does.
* Keep functions small and avoid duplicating logic.

## Tests

Run the full suite before opening a pull request:

```bash
python -m unittest discover -s tests -v
```

* Add or update tests in [`tests/test\_nova.py`](../tests/test_nova.py) for every behaviour change or bug fix.
* If you edited the Java files, check that they compile and run:

```bash
  javac -encoding UTF-8 -d out src/java/\*.java
  java -cp out nova.NovaEngine
  ```

* If you changed the chat page, open it in a browser and try a few messages, the quick-reply chips and the Clear button.

Also run the repository checker. It verifies links, heading anchors, badge text, the numbers quoted in the README, the HTML page, the Python and Java sources, JSON and YAML files and workflow paths:

```bash
python .github/scripts/check\_repo.py
```

GitHub Actions runs the tests on Python 3.10 to 3.13 and compiles the Java files on JDK 17 and 21 ([`ci.yml`](workflows/ci.yml)), and runs the checker on every push and once a day ([`repo-check.yml`](workflows/repo-check.yml)). Please don't say something works in a pull request unless you ran it.

## Pull requests

1. Fork the repository and create a branch from `main`, for example `fix-date-offset` or `brain-cooking-topic`.
2. Keep each pull request focused on one change.
3. Add a line under an *Unreleased* heading in [`CHANGELOG.md`](../CHANGELOG.md).
4. Fill in the pull request template: what changed, why, and how you tested it.
5. Make sure the CI checks pass.

Commit messages should be short and in the imperative mood, such as `Fix offset parsing for long numbers`.

## Reporting bugs and requesting features

Use the [issue forms](https://github.com/gelowie/nova-chatbot/issues/new/choose). For a bug, include the exact message you sent, the reply you expected, your Nova version, Python version and operating system, and any output from the terminal running `server.py`.

## Security

Nova has no login and is meant to listen on `127.0.0.1` only. Please report vulnerabilities privately as described in the [security policy](SECURITY.md), not in a public issue.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](../LICENSE).

