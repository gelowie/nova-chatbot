from __future__ import annotations

import ast
import operator
import re

# Allowed operators
_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Word operators (order matters)
_WORD_OPS: list[tuple[str, str]] = [
    (r"to the power of", "^"),
    (r"multiplied by", "*"),
    (r"multiply by", "*"),
    (r"divided by", "/"),
    (r"divide by", "/"),
    (r"take away", "-"),
    (r"added to", "+"),
    (r"\s*squared", "^2"),
    (r"\s*cubed", "^3"),
    (r"\bplus\b", "+"),
    (r"\bminus\b", "-"),
    (r"\btimes\b", "*"),
    (r"\bover\b", "/"),
    (r"\bmodulo\b", "%"),
    (r"\bmod\b", "%"),
    (r"\bpower\b", "^"),
    (r"\bpercent\b", "%"),
]

# Leading filler
_FILLERS = re.compile(
    r"^\s*(?:hey|hi|hello|nova|please|pls|"
    r"can you|could you|would you|"
    r"what(?:'s| is)?|whats|"
    r"how much is|how many is|how much|"
    r"calculate|compute|solve|evaluate|work out|"
    r"tell me|give me|show me|answer|equals?)\s+",
    re.IGNORECASE,
)

_ALLOWED = re.compile(r"^[\d+\-*/%^().\s]+$")


# Prompt to expression
def normalize_math(text: str) -> str | None:
    """Turn a natural-language prompt into plain arithmetic, or None if it isn't one."""
    expr = text.lower().strip().replace(",", "")
    expr = re.sub(r"[?!=]", " ", expr).replace("÷", "/").replace("×", "*")

    for _ in range(6):
        stripped = _FILLERS.sub("", expr, count=1)
        if stripped == expr:
            break
        expr = stripped

    # Percent-of has to run before "percent" becomes "%"
    expr = re.sub(r"(\d+(?:\.\d+)?)\s*(?:%|percent)\s*of\s*", r"(\1/100)*", expr)

    # "x" only counts as times between digits
    expr = re.sub(r"(?<=\d)\s*x\s*(?=\d)", "*", expr)

    for pattern, symbol in _WORD_OPS:
        expr = re.sub(pattern, symbol, expr)

    expr = expr.replace("^", "**")
    expr = re.sub(r"\s+", " ", expr).strip().rstrip("+*/^")

    # Validation gates
    has_digit = re.search(r"\d", expr)
    has_operator = re.search(r"[+\-*/%]", expr.replace("**", "*"))
    return expr if has_digit and has_operator and _ALLOWED.match(expr) else None


# Safe evaluator
def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError("non-numeric literal")

    if isinstance(node, ast.BinOp):
        op = _BINOPS.get(type(node.op))
        if op is None:
            raise ValueError(f"operator {type(node.op).__name__} not allowed")

        lhs, rhs = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and rhs == 0:
            raise ZeroDivisionError("division by zero")
        # Stops 9**9**9 from eating memory
        if isinstance(node.op, ast.Pow) and abs(rhs) > 64:
            raise ValueError("exponent too large")

        result = op(lhs, rhs)
        if isinstance(result, complex):
            raise ValueError("complex result")
        return result

    if isinstance(node, ast.UnaryOp):
        op = _UNARYOPS.get(type(node.op))
        if op is None:
            raise ValueError("unary operator not allowed")
        return op(_eval_node(node.operand))

    raise ValueError(f"disallowed syntax: {type(node).__name__}")


def _fmt(value: float) -> str:
    if isinstance(value, int):
        return str(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:.10g}"


# Public entry point
def solve(raw: str) -> str | None:
    """Answer a math prompt like "whats 5 plus 3 times 2", or None if it isn't math."""
    expression = normalize_math(raw)
    if expression is None:
        return None

    try:
        shown = _fmt(_eval_node(ast.parse(expression, mode="eval")))
    except ZeroDivisionError:
        return "I can't divide by zero — that one breaks the universe."
    except (OverflowError, ValueError) as err:
        # Huge ints fail in str() with a "digits" ValueError
        if isinstance(err, OverflowError) or "digits" in str(err):
            return "That result is too large for me to display."
        return None
    except (SyntaxError, RecursionError):
        return None

    pretty = expression.replace("**", "^").replace("*", " × ").replace("/", " ÷ ")
    pretty = re.sub(r"\s+", " ", pretty).strip()
    return f"Solved **{pretty}** = **{shown}**"


# Self-test
if __name__ == "__main__":
    prompts = [
        "whats 5 plus 3 times 2",
        "hey can you calculate 144 divided by 12",
        "15% of 200",
        "2^10",
        "100 / 0",
        "(12 + 8) / 4",
        "-5 + 10",
        "5 x 3",
        "3 squared plus 4 squared",
        "20 modulo 7",
        "hello",
        "tell me a joke",
        "5",
        "what time is it",
    ]
    for prompt in prompts:
        print(f"{prompt:<42} → {solve(prompt)}")
