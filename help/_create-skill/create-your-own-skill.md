# Create your own skill

A **skill** is a small Python module that answers one kind of message *exactly*, before the fuzzy JSON brain gets a chance. Nova's two built-in skills are math (`src/py/math_solver.py`) and time (`src/py/time_reader.py`).

This walkthrough adds a **dice roller** ("roll 2d6"). It was tested against this repository: the code below works as written.

## 1. Write the module

Create `src/py/dice_roller.py`:

```python
"""Dice skill: answers messages such as "roll 2d6" or "roll a d20"."""

from __future__ import annotations

import random
import re

_ROLL = re.compile(r"\broll\s+(?:an?\s+)?(\d*)d(\d+)\b", re.IGNORECASE)

MAX_DICE = 20
MAX_SIDES = 1000


def handle(message: str) -> str | None:
    """Return a reply if `message` is a dice request, otherwise None."""
    match = _ROLL.search(message)
    if not match:
        return None  # not for this skill: let the next layer try

    count = int(match.group(1) or 1)
    sides = int(match.group(2))
    if not (1 <= count <= MAX_DICE and 2 <= sides <= MAX_SIDES):
        return f"I can roll 1-{MAX_DICE} dice with 2-{MAX_SIDES} sides each."

    rolls = [random.randint(1, sides) for _ in range(count)]
    return f"Rolled **{count}d{sides}**: {', '.join(map(str, rolls))} (total **{sum(rolls)}**)"
```

## 2. Register it

In `src/py/engine.py`, import the module and add it to the list of skills in `respond()`:

```python
from . import dice_roller, math_solver, time_reader
...
        for skill_name, handler in (
            ("math", math_solver.solve),
            ("time", time_reader.handle),
            ("dice", dice_roller.handle),
        ):
```

Skills are tried in the order listed. The first one that returns a non-empty string wins; if all return `None`, the message goes to the JSON brain.

## 3. Try it

Restart `python server.py` and send `roll 2d6`:

```
Rolled **2d6**: 3, 3 (total **6**)
```

The `skill` field of the API response is `"dice"`.

## 4. Test it

Add a test method to the `EngineTests` class in `tests/test_nova.py` (the class that has `self.engine`). Avoid asserting on the random numbers; checking the routing and the limits is enough:

```python
def test_dice_routing(self):
    reply = self.engine.respond("roll 2d6")
    self.assertEqual(reply["skill"], "dice")
    self.assertEqual(self.engine.respond("roll 99d6")["skill"], "dice")  # limit message
    self.assertEqual(self.engine.respond("hello")["skill"], "brain")
```

Then run `python -m unittest discover -s tests -v`.

## 5. Document it

Mention the skill in the README feature list and in `CHANGELOG.md` under a new *Unreleased* heading.

## Things to know

- A skill added in Python is **not** added to the Java implementation automatically. The Java engine (`src/java/NovaEngine.java`) calls its two skills directly. Say so in your pull request if the two differ.
- Skills must be deterministic and safe: never pass user text to `eval()`, `exec()` or a shell.
- Keep a skill narrow. Answer only messages you are sure about and return `None` for everything else, otherwise it will swallow ordinary chat (the time skill once answered "i feel great today" for exactly this reason).

More detail: [how to create a skill](how-to-create-skill.md) · [what a skill receives and returns](how-to-input-skill.md) · [naming](how-to-name-skill.md).
