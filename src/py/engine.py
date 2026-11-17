from __future__ import annotations

import json
import random
import re
from pathlib import Path

from . import math_solver, time_reader

# Fallback chips for math and time replies
_DEFAULT_CHIPS = ["Tell me a joke", "What can you do?", "What time is it?"]

# Skills before the brain, math first
_SKILLS = (("math", math_solver.solve), ("time", time_reader.handle))

_MATCH_THRESHOLD = 0.35
_CONTAINS_SCORE = 0.95
_MAX_REDRAWS = 12


class NovaEngine:
    def __init__(self, brain_path: str | Path):
        self.brain = json.loads(Path(brain_path).read_text(encoding="utf-8"))
        self._last: dict[str, int] = {}

        # Slang and typo fixes in one map
        self._fixes: dict[str, str] = {
            **self.brain.get("phraseFixes", {}),
            **self.brain.get("typos", {}),
        }

        # Patterns normalized once at load
        self._patterns: list[tuple[dict, set[str], re.Pattern[str]]] = [
            (intent, set(norm.split()), self._inside_regex(norm))
            for intent in self.brain["intents"]
            for pattern in intent["patterns"]
            if (norm := self._normalize(pattern))
        ]

    def respond(self, message: str) -> dict:
        """Route a message; returns {"text", "skill", "suggestions"}."""
        message = (message or "").strip()
        if not message:
            return self._fallback()

        # Local skills
        for name, handler in _SKILLS:
            if answer := handler(message):
                return {"text": answer, "skill": name, "suggestions": _DEFAULT_CHIPS}

        # JSON brain
        if intent := self._match_intent(message):
            return {
                "text": self._pick(intent),
                "skill": "brain",
                "suggestions": intent.get("suggestions", _DEFAULT_CHIPS),
            }

        return self._fallback()

    # Text normalization
    def _normalize(self, text: str) -> str:
        norm = re.sub(r"[^a-z0-9'\s]", " ", f" {text.lower().strip()} ")
        # Longest fixes first
        for slang in sorted(self._fixes, key=len, reverse=True):
            norm = re.sub(rf"\b{re.escape(slang)}\b", self._fixes[slang], norm)
        return re.sub(r"\s+", " ", norm).strip()

    @staticmethod
    def _inside_regex(pattern: str) -> re.Pattern[str]:
        # Whole-word match, stretched last letter allowed
        return re.compile(
            rf"(?<![a-z0-9']){re.escape(pattern)}{re.escape(pattern[-1])}*(?![a-z0-9'])"
        )

    # Intent matching
    def _match_intent(self, text: str) -> dict | None:
        norm = self._normalize(text)
        tokens = set(norm.split())
        if not tokens:
            return None

        best: dict | None = None
        best_score = 0.0
        for intent, pattern_tokens, inside in self._patterns:
            overlap = len(tokens & pattern_tokens) / len(tokens | pattern_tokens)
            if inside.search(norm):
                overlap = max(overlap, _CONTAINS_SCORE)

            score = overlap * intent.get("priority", 1.0)
            if score > best_score:
                best, best_score = intent, score

        # Cutoff chosen empirically
        return best if best_score >= _MATCH_THRESHOLD else None

    def _pick(self, intent: dict) -> str:
        responses = intent.get("responses") or ["..."]
        if len(responses) == 1:
            return responses[0]

        tag = intent.get("tag", "")
        idx = random.randrange(len(responses))
        for _ in range(_MAX_REDRAWS):
            if idx != self._last.get(tag):
                break
            idx = random.randrange(len(responses))
        self._last[tag] = idx
        return responses[idx]

    def _fallback(self) -> dict:
        meta = self.brain["meta"]
        return {
            "text": random.choice(meta["fallbacks"]),
            "skill": "fallback",
            "suggestions": meta.get("unknownSuggestions", []),
        }


# Self-test
if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    engine = NovaEngine(here.parent / "json" / "brain.json")

    prompts = [
        "whats 5 plus 3 times 2",
        "144 divided by 12",
        "100 / 0",
        "what time is it",
        "what day is it today",
        "what is the date next month",
        "hello there",
        "helo",
        "u there?",
        "tell me a joke",
        "i am bored",
        "i am sad",
        "thanks!",
        "asdfghjkl",
    ]
    for prompt in prompts:
        reply = engine.respond(prompt)
        preview = reply["text"].splitlines()[0][:70]
        print(f"[{reply['skill'].ljust(8)}] {prompt:<34} → {preview}")
