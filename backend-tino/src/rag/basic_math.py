from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
import unicodedata


_NUMBER = r"-?\d+(?:[.,]\d+)?"
_SYMBOL_OPERATION_RE = re.compile(
    rf"(?<!\w)(?P<a>{_NUMBER})\s*(?P<op>[+\-*/xX×÷])\s*(?P<b>{_NUMBER})(?!\w)"
)
_WORD_OPERATION_RE = re.compile(
    rf"(?:cuanto\s+es\s+)?(?P<a>{_NUMBER})\s+"
    rf"(?P<op>mas|menos|por|multiplicado\s+por|dividido\s+entre|dividido\s+por)\s+"
    rf"(?P<b>{_NUMBER})"
)
_COMMAND_OPERATION_RE = re.compile(
    rf"\b(?P<op>suma|resta|multiplica|divide)\s+"
    rf"(?P<a>{_NUMBER})\s+(?:y|con|por|entre|de)\s+(?P<b>{_NUMBER})\b"
)
_MATH_LIKE_RE = re.compile(
    rf"({_NUMBER}\s*[+\-*/xX×÷]\s*{_NUMBER})|"
    r"\b(cuanto\s+es|suma|resta|multiplica|divide|mas|menos|multiplicado\s+por|"
    r"dividido\s+entre|dividido\s+por)\b"
)

_ALLOWED_PREFIX_RE = re.compile(
    r"^\s*(?:cuanto\s+es|cuanto\s+da|calcula|resuelve|dime|"
    r"suma|resta|multiplica|divide)?\s*",
    re.IGNORECASE,
)


def solve_basic_math_query(query: str) -> str | None:
    """
    Solve one simple arithmetic operation without eval/code execution.
    Returns None when the message is not a safe basic math query.
    """
    normalized = _normalize_query(query)
    if not normalized:
        return None

    match = _SYMBOL_OPERATION_RE.search(normalized)
    if not match:
        match = _WORD_OPERATION_RE.search(normalized)
    if not match:
        match = _COMMAND_OPERATION_RE.search(normalized)
    if not match:
        return None

    if not _looks_like_simple_math(normalized, match):
        return None

    try:
        left = _parse_number(match.group("a"))
        right = _parse_number(match.group("b"))
    except InvalidOperation:
        return None

    op = _normalize_operator(match.group("op"))
    if op == "/" and right == 0:
        return "No se puede dividir entre cero."

    result = _apply(left, right, op)
    return f"Claro 🐦✨ {_format_number(left)} {_display_operator(op)} {_format_number(right)} = {_format_number(result)}."


def is_basic_math_like_query(query: str) -> bool:
    text = _normalize_query(query)
    if not _MATH_LIKE_RE.search(text):
        return False
    if not re.search(_NUMBER, text):
        return False
    return not any(term in text for term in ("precio", "costo", "cuesta", "inversion", "cop", "$"))


def _normalize_query(query: str) -> str:
    text = query.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("¿", "").replace("?", "").replace("¡", "").replace("!", "")
    text = re.sub(r"\s+", " ", text)
    return text


def _looks_like_simple_math(text: str, match: re.Match[str]) -> bool:
    if len(re.findall(_NUMBER, text)) != 2:
        return False
    if any(token in text for token in ("=", "**", "//", "%", "sqrt", "raiz", "potencia", "porcentaje")):
        return False
    prefix = text[: match.start()]
    suffix = text[match.end() :]
    if _ALLOWED_PREFIX_RE.sub("", prefix).strip():
        return False
    if suffix.strip():
        return False
    return True


def _parse_number(value: str) -> Decimal:
    return Decimal(value.replace(",", "."))


def _normalize_operator(op: str) -> str:
    compact = re.sub(r"\s+", " ", op.lower()).strip()
    if compact in {"+", "mas", "suma"}:
        return "+"
    if compact in {"-", "menos", "resta"}:
        return "-"
    if compact in {"*", "x", "×", "por", "multiplicado por", "multiplica"}:
        return "*"
    return "/"


def _apply(left: Decimal, right: Decimal, op: str) -> Decimal:
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    return left / right


def _display_operator(op: str) -> str:
    return op


def _format_number(value: Decimal) -> str:
    if value == value.to_integral():
        return str(value.quantize(Decimal("1")))
    return format(value.normalize(), "f").rstrip("0").rstrip(".")
