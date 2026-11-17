# How to create a skill (checklist)

The short version of the [full walkthrough](create-your-own-skill.md).

1. **Decide the job.** One skill answers one kind of message exactly (arithmetic, dates, dice). Open-ended chat belongs in the [JSON brain](../the-json-brain.md), not in a skill.
2. **Create the module** `src/py/<name>.py` with a function `handle(message: str) -> str | None`.
3. **Return `None` when the message is not yours.** Only return text when you are sure.
4. **Register it** in `src/py/engine.py`: import the module and add `("<label>", <module>.handle)` to the tuple in `respond()`. Order matters: put narrow, high-confidence skills first.
5. **Test it** in `tests/`, including messages that must *not* trigger it.
6. **Run the suite**: `python -m unittest discover -s tests -v`.
7. **Update the docs** (README, `CHANGELOG.md`).

Nothing else needs to change: the server, the frontend and the API format already handle any skill, because the reply is the same `{text, skill, suggestions}` object.
