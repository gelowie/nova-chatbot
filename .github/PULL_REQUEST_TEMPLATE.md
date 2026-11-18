## What does this change?

Added repo checker script.

- New `.github/scripts/check_repo.py` (standard library only). It checks Markdown links and heading anchors, path letter case, badge text against the real version/license/Python minimum, the numbers quoted in the README against `brain.json`, the HTML page and its JavaScript, Python and Java sources, JSON and YAML files, and paths used in workflows.
- New `.github/workflows/repo-check.yml`. It runs on every push and pull request and once a day. A separate daily job checks outside links, and a failed daily run opens an issue.
- `ci.yml` now also runs daily, and Dependabot checks GitHub Actions versions daily.
- `CONTRIBUTING.md`, the pull request template, the README, the four translated READMEs and `docs/img/_img.md` now mention the checker.

No issue to close.

## Type of change

- [ ] Bug fix
- [ ] New feature or skill
- [ ] Brain update (`src/json/brain.json`)
- [x] Documentation
- [ ] Refactor or code quality
- [ ] Tests

This is also a CI and tooling change. The template has no box for that, so I only ticked Documentation.

## How was it tested?

- `python -m unittest discover -s tests -v`: 28 tests pass.
- `python .github/scripts/check_repo.py`: 0 errors, 1 warning. The warning is the pattern "how is your day" being used by two brain topics, which I left unchanged.
- The checker also reports errors correctly when I deliberately break a copy of the repo (broken links, wrong case, bad badge text, unclosed HTML tag, JavaScript syntax error, wrong Java class name, duplicate brain tag, bad workflow path, third-party import).
- The Java sources compile with `javac -Xlint:all`.
- The new workflows can only be fully verified by running on GitHub, so please check the Actions tab on this PR.

## Checklist

- [x] I read the [contributing guide](https://github.com/gelowie/nova-chatbot/blob/main/.github/CONTRIBUTING.md)
- [x] `python -m unittest discover -s tests -v` passes
- [x] `python .github/scripts/check_repo.py` reports no errors
- [ ] I added or updated tests for the behavior I changed (not applicable: no Nova behavior changed)
- [ ] If I changed the math or time skill, I updated the matching Java file and it compiles (not applicable: Java unchanged)
- [ ] I tried my change in the chat page (not applicable: the page is unchanged)
- [x] I updated the docs and added a line to `CHANGELOG.md` under *Unreleased* (docs updated; the changelog is intentionally unchanged for repository tooling)
- [x] My change adds no dependency and makes no outgoing network call (Nova itself is unchanged; the workflow installs PyYAML only inside CI, and the checker's optional `--external` mode makes network requests when run on purpose)
