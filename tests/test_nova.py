"""Regression tests for Nova's Python implementation.

Run from the repo root: python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.py import NovaEngine, math_solver, time_reader  # noqa: E402

BRAIN_PATH = ROOT / "src" / "json" / "brain.json"


class BrainFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brain = json.loads(BRAIN_PATH.read_text(encoding="utf-8"))

    def test_top_level_sections(self):
        for key in ("meta", "typos", "phraseFixes", "intents"):
            self.assertIn(key, self.brain)

    def test_intents_are_well_formed(self):
        tags = [i["tag"] for i in self.brain["intents"]]
        self.assertEqual(len(tags), len(set(tags)), "duplicate intent tags")
        for intent in self.brain["intents"]:
            self.assertTrue(intent["patterns"], intent["tag"])
            self.assertTrue(intent["responses"], intent["tag"])
            for text in intent["patterns"] + intent["responses"]:
                self.assertIsInstance(text, str)
                self.assertTrue(text.strip(), intent["tag"])

    def test_no_unfinished_placeholder_replies(self):
        for intent in self.brain["intents"]:
            for text in intent["responses"]:
                self.assertFalse(text.strip().endswith(": ..."), (intent["tag"], text))

    def test_fallbacks_exist(self):
        self.assertTrue(self.brain["meta"]["fallbacks"])


class MathTests(unittest.TestCase):
    CASES = {
        "whats 5 plus 3 times 2": "= **11**",
        "144 divided by 12": "= **12**",
        "100 - 45 + 12": "= **67**",
        "15% of 200": "= **30**",
        "10 percent of 50": "= **5**",
        "2^10": "= **1024**",
        "(12 + 8) / 4": "= **5**",
        "-5 + 10": "= **5**",
        "5 x 3": "= **15**",
        "5 × 3": "= **15**",
        "20 modulo 7": "= **6**",
        "3 squared plus 4 squared": "= **25**",
        "1000 times 1000": "= **1000000**",
        "144 * 12345": "= **1777680**",
        "1/3": "= **0.3333333333**",
        "0.1 + 0.2": "= **0.3**",
    }

    def test_known_answers(self):
        for text, expected in self.CASES.items():
            with self.subTest(text=text):
                result = math_solver.solve(text)
                self.assertIsNotNone(result)
                self.assertTrue(result.endswith(expected), result)

    def test_division_by_zero(self):
        self.assertIn("divide by zero", math_solver.solve("100 / 0"))

    def test_not_math(self):
        for text in ("hello", "5", "tell me a joke", "5+", "1.2.3 + 1"):
            with self.subTest(text=text):
                self.assertIsNone(math_solver.solve(text))

    def test_huge_result_does_not_crash(self):
        self.assertIsNotNone(math_solver.solve(("9" * 400) + "^64"))


class TimeTests(unittest.TestCase):
    MUST_ANSWER = [
        "what time is it", "current time", "tell me the time", "time now",
        "what is the time", "do you know the time", "got the time",
        "what's the time", "time?", "what is the date", "what day is it",
        "today date", "what is today", "current date", "tell me the date",
        "what is the date next month", "what was the date last month",
        "what will the date be in 3 weeks", "date in 5 days", "in 2 months",
        "3 weeks from now", "what is tomorrow", "what was yesterday",
        "what day is tomorrow", "what's tomorrow", "tomorrow", "yesterday",
        "what is the date tomorrow", "what day is it tomorrow",
        "tomorrow's date", "yesterday's date",
    ]
    MUST_IGNORE = [
        "i feel great today", "how do you feel today", "weather today",
        "coffee time", "sometimes i feel sad", "what is an update",
        "i have 2 days off", "i need a pastime", "hello", "tell me a joke",
        "i think about you all the time", "it has been 3 weeks",
        "see you tomorrow", "bye, talk tomorrow", "i was sad yesterday",
        "what are we doing tomorrow",
    ]

    def test_answers_time_questions(self):
        for text in self.MUST_ANSWER:
            with self.subTest(text=text):
                self.assertIsNotNone(time_reader.handle(text))

    def test_ignores_ordinary_chat(self):
        for text in self.MUST_IGNORE:
            with self.subTest(text=text):
                self.assertIsNone(time_reader.handle(text))

    def test_what_day_is_tomorrow_names_tomorrow(self):
        expected = time_reader.pretty_date(date.today() + timedelta(days=1))
        self.assertIn(expected, time_reader.handle("what day is tomorrow"))

    def test_tomorrow_is_correct(self):
        expected = time_reader.pretty_date(date.today() + timedelta(days=1))
        self.assertIn(expected, time_reader.handle("what is tomorrow"))

    def test_month_arithmetic_clamps_once(self):
        self.assertEqual(time_reader.add_months(date(2026, 1, 31), 2), date(2026, 3, 31))
        self.assertEqual(time_reader.add_months(date(2026, 3, 31), -1), date(2026, 2, 28))
        self.assertEqual(time_reader.add_months(date(2024, 1, 31), 1), date(2024, 2, 29))
        self.assertEqual(time_reader.add_months(date(2026, 12, 15), 1), date(2027, 1, 15))

    def test_offset_cap(self):
        self.assertIn("too far", time_reader.handle("date in 99999999 days"))
        self.assertIn("That lands on", time_reader.handle("date in 10000 days"))


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = NovaEngine(BRAIN_PATH)

    def test_response_shape(self):
        reply = self.engine.respond("hello")
        self.assertEqual(set(reply), {"text", "skill", "suggestions"})
        self.assertTrue(reply["text"])

    def test_skill_routing(self):
        self.assertEqual(self.engine.respond("2 + 2")["skill"], "math")
        self.assertEqual(self.engine.respond("what time is it")["skill"], "time")
        self.assertEqual(self.engine.respond("hello")["skill"], "brain")

    def test_typos_and_slang(self):
        for text in ("helo", "hru", "sup", "thx", "wat r u doin", "helloooo thereeee"):
            with self.subTest(text=text):
                self.assertEqual(self.engine.respond(text)["skill"], "brain")

    def test_fallback_and_empty(self):
        for text in ("asdfghjkl", "???", ""):
            with self.subTest(text=text):
                self.assertEqual(self.engine.respond(text)["skill"], "fallback")

    def test_every_brain_pattern_is_answered(self):
        # Brain patterns must not be swallowed by a skill
        for intent in self.engine.brain["intents"]:
            if intent["tag"] in ("time", "date", "math_help"):
                continue
            for pattern in intent["patterns"]:
                with self.subTest(pattern=pattern):
                    self.assertNotIn(self.engine.respond(pattern)["skill"], ("math", "time"))

    def _tag(self, text):
        intent = self.engine._match_intent(text)
        return intent["tag"] if intent else None

    def test_short_patterns_do_not_match_inside_words(self):
        # Short patterns must not match inside longer words
        self.assertIsNone(self._tag("this is nice"))
        self.assertIsNone(self._tag("i know"))
        self.assertEqual(self._tag("that helped a lot"), "thanks")
        self.assertEqual(self._tag("see you tomorrow"), "goodbye")
        self.assertEqual(self._tag("what do you think about music"), "music")

    def test_stretched_words_still_match(self):
        for text, tag in (("heyyy", "greeting"), ("hiii", "greeting"),
                          ("byeee", "goodbye"), ("noooo", "no"),
                          ("helloooo thereeee", "greeting")):
            with self.subTest(text=text):
                self.assertEqual(self._tag(text), tag)

    def test_chat_with_today_is_not_a_date_question(self):
        self.assertEqual(self.engine.respond("i feel great today")["skill"], "brain")


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import server

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path):
        try:
            with urllib.request.urlopen(self.base + path) as resp:
                return resp.status, resp.read(), resp.headers
        except urllib.error.HTTPError as err:
            return err.code, err.read(), err.headers

    def _post(self, body: bytes):
        req = urllib.request.Request(
            self.base + "/chat", data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def test_health(self):
        status, body, _ = self._get("/health")
        self.assertEqual((status, json.loads(body)), (200, {"ok": True}))

    def test_frontend_and_icon(self):
        status, body, headers = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn(b"Nova", body)
        self.assertEqual(self._get("/?cache=1")[0], 200)
        status, body, headers = self._get("/docs/img/icon.png")
        self.assertEqual((status, headers["Content-Type"]), (200, "image/png"))
        self.assertTrue(body.startswith(b"\x89PNG"))

    def test_nothing_else_is_served(self):
        for path in ("/server.py", "/src/json/brain.json", "/docs/img/banner.png"):
            with self.subTest(path=path):
                self.assertEqual(self._get(path)[0], 404)

    def test_chat(self):
        status, data = self._post(json.dumps({"message": "whats 5 plus 3 times 2"}).encode())
        self.assertEqual(status, 200)
        self.assertEqual(data["skill"], "math")
        self.assertIn("**11**", data["text"])

    def test_bad_requests(self):
        for body in (b"not json", b"[]", b'{"message": 5}', b"\xff\xfe"):
            with self.subTest(body=body):
                status, data = self._post(body)
                self.assertEqual(status, 400)
                self.assertIn("error", data)

    def test_oversized_body(self):
        body = json.dumps({"message": "a" * 70_000}).encode()
        try:
            status, _ = self._post(body)
        except (urllib.error.URLError, ConnectionError, OSError):
            # Server may hang up before the upload finishes
            return
        self.assertEqual(status, 413)


if __name__ == "__main__":
    unittest.main()
