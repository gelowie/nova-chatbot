# Naming a skill

Consistent names make the codebase easy to scan.

| Thing | Convention | Existing examples |
|---|---|---|
| Module file | `snake_case.py` in `src/py/`, named for the job (a noun phrase) | `math_solver.py`, `time_reader.py`, `dice_roller.py` (from the walkthrough) |
| Entry function | `handle(message)` | `time_reader.handle`. (`math_solver.solve` predates this convention; new skills should use `handle`.) |
| Skill label | Short, lowercase single word, registered in `engine.py` | `"math"`, `"time"` |
| Brain intent tag | lowercase `snake_case`, unique | `how_are_you`, `bot_name` |
| Tests | Added to `tests/`, named for what they check | `test_dice_routing` |

The **skill label** is public: it is returned as the `skill` field of every `POST /chat` response (alongside the reserved labels `brain`, `fallback` and `error`), so choose it once and keep it stable. Do not reuse a reserved label.

Java: if you also port the skill, use the same name in PascalCase (`DiceRoller.java`) so the two implementations are easy to compare.
