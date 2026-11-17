from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timedelta

MAX_OFFSET = 10_000


# Clock readings
def current_time(fmt: str = "%H:%M") -> str:
    return datetime.now().strftime(fmt)


def current_datetime() -> str:
    return datetime.now().strftime("%A, %d %B %Y at %H:%M:%S")


def current_date() -> date:
    return date.today()


def day_name(d: date | None = None) -> str:
    return (d or date.today()).strftime("%A")


def pretty_date(d: date | None = None) -> str:
    return (d or date.today()).strftime("%A, %d %B %Y")


def iso_date(d: date | None = None) -> str:
    return (d or date.today()).isoformat()


# Calendar arithmetic
def add_months(d: date, months: int) -> date:
    """Clamp the day once, to the target month, so 31 Jan + 2 months is 31 Mar (as java.time does)."""
    year, month0 = divmod(d.year * 12 + d.month - 1 + months, 12)
    month = month0 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def next_month(d: date | None = None) -> date:
    return add_months(d or date.today(), 1)


def previous_month(d: date | None = None) -> date:
    return add_months(d or date.today(), -1)


def shift(days: int = 0, weeks: int = 0, months: int = 0) -> date:
    return add_months(date.today() + timedelta(days=days + weeks * 7), months)


# Detection rules
_REL = re.compile(r"\b(\d+)\s*(days?|weeks?|months?)\b", re.IGNORECASE)

# Offsets need a cue
_REL_CUE = re.compile(
    r"\b(?:in|after|add)\s+\d+\s*(?:days?|weeks?|months?)\b"
    r"|\bdate\b|\bfrom (?:now|today)\b"
)

# Whole-word checks
_TIME_Q = re.compile(
    r"\b(?:what time|current time|time now|time please|clock"
    r"|(?:what(?:'s| is)?|whats|tell me|know|got|have|give me|check) the time)\b"
    r"|^\W*time\W*$"
)
_DATE_Q = re.compile(r"\bdate\b|\b(?:what is|what's|whats) today\b|^\W*today\W*$")
_WEEKDAY_Q = re.compile(r"\b(?:what day|which day|day of the week|name of the day)\b")

# Tomorrow and yesterday need a cue
_DAY_CUE = (
    r"(?:what(?:'s| is| was| will)?|whats|which|tell me|give me)\s+"
    r"(?:the\s+)?(?:date\s+|day\s+)?(?:is\s+|was\s+|of\s+|for\s+)?(?:it\s+)?"
)


def _day_question(word: str) -> re.Pattern[str]:
    return re.compile(
        rf"^\W*{word}\W*$"
        rf"|\b{_DAY_CUE}{word}\b"
        rf"|\b{word}'?s?\s+(?:date|day)\b"
        rf"|\bdate\s+(?:of|for)\s+{word}\b"
    )


_TOMORROW_Q = _day_question("tomorrow")
_YESTERDAY_Q = _day_question("yesterday")
_NEXT_MONTH_Q = re.compile(r"\b(?:next month|following month|a month from now)\b")
_LAST_MONTH_Q = re.compile(r"\b(?:last month|previous month|a month ago)\b")


# Public entry point
def handle(raw: str) -> str | None:
    """Answer a time or date question, or None if the prompt isn't one."""
    q = (raw or "").lower().strip()
    if not q:
        return None

    # Relative offsets ("date in 3 weeks")
    if (m := _REL.search(q)) and _REL_CUE.search(q):
        digits, unit = m.group(1).lstrip("0") or "0", m.group(2).lower()
        # Length check first: int() refuses strings past 4300 digits
        if len(digits) > 6 or int(digits) > MAX_OFFSET:
            return (f"That's too far away for me to work out reliably — "
                    f"try {MAX_OFFSET:,} or fewer.")
        amount = int(digits)
        if "week" in unit:
            target = shift(weeks=amount)
        elif "month" in unit:
            target = shift(months=amount)
        else:
            target = shift(days=amount)
        return f"That lands on **{pretty_date(target)}** ({iso_date(target)})."

    if any(phrase in q for phrase in ("date and time", "full date", "timestamp")):
        return f"It's **{current_datetime()}** right now."

    # Before the weekday check
    if _TOMORROW_Q.search(q):
        return f"Tomorrow is **{pretty_date(shift(days=1))}**."
    if _YESTERDAY_Q.search(q):
        return f"Yesterday was **{pretty_date(shift(days=-1))}**."

    if _WEEKDAY_Q.search(q):
        today = current_date()
        return f"Today is **{day_name(today)}** — {pretty_date(today)} ({iso_date(today)})."

    if _NEXT_MONTH_Q.search(q):
        target = next_month()
        return f"One month from today will be **{pretty_date(target)}** ({iso_date(target)})."
    if _LAST_MONTH_Q.search(q):
        target = previous_month()
        return f"One month before today was **{pretty_date(target)}** ({iso_date(target)})."

    if _TIME_Q.search(q):
        return f"It's **{current_time()}** on your system clock."

    # Broadest check, so it goes last
    if _DATE_Q.search(q):
        return f"Today is **{pretty_date()}** ({iso_date()})."

    return None


# Self-test
if __name__ == "__main__":
    prompts = [
        "what time is it",
        "what day is it today",
        "what is the date",
        "what is the date next month",
        "what was the date last month",
        "what will the date be in 3 weeks",
        "date in 5 days",
        "what is tomorrow",
        "what was yesterday",
        "full date and time please",
        "tell me a joke",
        "whats 5 plus 3",
    ]
    for prompt in prompts:
        print(f"{prompt:<42} → {handle(prompt)}")
