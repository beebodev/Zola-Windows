"""Bounded Decimal arithmetic evaluator for the zola_tools calculate tool — P6-D08."""

from __future__ import annotations

import ast
import re
import time
from decimal import (
    ROUND_CEILING,
    ROUND_FLOOR,
    ROUND_HALF_UP,
    Context,
    Decimal,
    DecimalException,
    localcontext,
)
from typing import Any, Callable, Dict, List, Optional, Set, Type

# P6-CALC: named limits and allowlists — P6-D08
MAX_INPUT_LENGTH = 500
MAX_NODE_COUNT = 128
MAX_ABS_EXPONENT = 1000
MAX_BASE_ABS_FOR_POW = Decimal("1000000")
MAX_RESULT_DIGITS = 40
MAX_OUTPUT_DECIMALS = 15
MIN_ROUND_NDIGITS = 0
MAX_ROUND_NDIGITS = 10
DECIMAL_PRECISION = 50
WALL_CLOCK_MS = 100

ERROR_INVALID_TYPE = "invalid_type"
ERROR_EMPTY_EXPRESSION = "empty_expression"
ERROR_INPUT_TOO_LONG = "input_too_long"
ERROR_SYNTAX = "syntax_error"
ERROR_UNSUPPORTED_NODE = "unsupported_node"
ERROR_UNSUPPORTED_NAME = "unsupported_name"
ERROR_UNSUPPORTED_FUNCTION = "unsupported_function"
ERROR_UNSUPPORTED_OPERATOR = "unsupported_operator"
HINT_UNSUPPORTED_OPERATOR = "for percent, use 0.15*240"
ERROR_ARITY = "arity_error"
ERROR_INVALID_ARGUMENT = "invalid_argument"
ERROR_DIVISION_BY_ZERO = "division_by_zero"
ERROR_NEGATIVE_SQRT = "negative_sqrt"
ERROR_EXPONENT_NOT_INTEGER = "exponent_not_integer"
ERROR_EXPONENT_OUT_OF_RANGE = "exponent_out_of_range"
ERROR_BASE_OUT_OF_RANGE = "base_out_of_range"
ERROR_NODE_LIMIT = "node_limit"
ERROR_RESULT_TOO_LARGE = "result_too_large"
ERROR_RESULT_TOO_SMALL = "result_too_small"
ERROR_TIMEOUT = "timeout"
ERROR_INVALID_LITERAL = "invalid_literal"

# P6-CALC: strict decimal literal (digits, optional fraction, optional exponent) — P6-D08
_LITERAL_PATTERN = re.compile(
    r"^(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$"
)

_ALLOWED_BINOPS: Set[Type[ast.operator]] = {
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
}

_REJECTED_BINOPS: Set[Type[ast.operator]] = {
    ast.Mod,
    ast.FloorDiv,
}

_ALLOWED_UNARY: Set[Type[ast.unaryop]] = {
    ast.UAdd,
    ast.USub,
}


class _CalcError(Exception):
    """Structured calculator failure; code is the JSON error value."""

    def __init__(self, code: str, hint: Optional[str] = None) -> None:
        self.code = code
        self.hint = hint
        super().__init__(code)


def _error_dict(code: str, hint: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"ok": False, "error": code}
    if hint is not None:
        payload["hint"] = hint
    return payload


def _check_result_digits(value: Decimal) -> Decimal:
    # P6-CALC: integer-part digits only (magnitude via adjusted()) — P6-D08
    if value != 0 and (value.adjusted() + 1) > MAX_RESULT_DIGITS:
        raise _CalcError(ERROR_RESULT_TOO_LARGE)
    return value


def _format_result(value: Decimal) -> str:
    if value == 0:
        return "0"
    # P6-CALC: round to MAX_OUTPUT_DECIMALS, then strip trailing zeros — P6-D08
    # Formatting may need prec > DECIMAL_PRECISION when integer digits approach 40.
    quant = Decimal("1").scaleb(-MAX_OUTPUT_DECIMALS)
    format_prec = DECIMAL_PRECISION + MAX_OUTPUT_DECIMALS + 5
    try:
        with localcontext(Context(prec=format_prec, rounding=ROUND_HALF_UP)):
            rounded = value.quantize(quant, rounding=ROUND_HALF_UP)
    except DecimalException:
        raise _CalcError(ERROR_INVALID_ARGUMENT) from None
    if rounded == 0:
        raise _CalcError(ERROR_RESULT_TOO_SMALL)
    text = format(rounded, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("", "-"):
        raise _CalcError(ERROR_RESULT_TOO_SMALL)
    return text


def _parse_literal(source: str, node: ast.Constant) -> Decimal:
    if node.end_col_offset is None:
        raise _CalcError(ERROR_INVALID_LITERAL)
    raw = source[node.col_offset:node.end_col_offset]
    if not _LITERAL_PATTERN.fullmatch(raw):
        raise _CalcError(ERROR_INVALID_LITERAL)
    if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
        raise _CalcError(ERROR_INVALID_LITERAL)
    try:
        return Decimal(raw)
    except (DecimalException, ValueError, ArithmeticError):
        raise _CalcError(ERROR_INVALID_LITERAL) from None


def _fn_abs(args: List[Decimal]) -> Decimal:
    if len(args) != 1:
        raise _CalcError(ERROR_ARITY)
    return abs(args[0])


def _fn_min(args: List[Decimal]) -> Decimal:
    if len(args) < 1:
        raise _CalcError(ERROR_ARITY)
    return min(args)


def _fn_max(args: List[Decimal]) -> Decimal:
    if len(args) < 1:
        raise _CalcError(ERROR_ARITY)
    return max(args)


def _fn_sqrt(args: List[Decimal]) -> Decimal:
    if len(args) != 1:
        raise _CalcError(ERROR_ARITY)
    if args[0] < 0:
        raise _CalcError(ERROR_NEGATIVE_SQRT)
    return args[0].sqrt()


def _fn_floor(args: List[Decimal]) -> Decimal:
    if len(args) != 1:
        raise _CalcError(ERROR_ARITY)
    return args[0].to_integral_value(rounding=ROUND_FLOOR)


def _fn_ceil(args: List[Decimal]) -> Decimal:
    if len(args) != 1:
        raise _CalcError(ERROR_ARITY)
    return args[0].to_integral_value(rounding=ROUND_CEILING)


def _fn_round(args: List[Decimal]) -> Decimal:
    if len(args) == 1:
        return args[0].quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if len(args) != 2:
        raise _CalcError(ERROR_ARITY)
    n = args[1]
    if n != n.to_integral_value():
        raise _CalcError(ERROR_INVALID_ARGUMENT)
    n_int = int(n)
    if n_int < MIN_ROUND_NDIGITS or n_int > MAX_ROUND_NDIGITS:
        raise _CalcError(ERROR_INVALID_ARGUMENT)
    quant = Decimal("1").scaleb(-n_int)
    return args[0].quantize(quant, rounding=ROUND_HALF_UP)


_FUNCTIONS: Dict[str, Callable[[List[Decimal]], Decimal]] = {
    "abs": _fn_abs,
    "min": _fn_min,
    "max": _fn_max,
    "sqrt": _fn_sqrt,
    "floor": _fn_floor,
    "ceil": _fn_ceil,
    "round": _fn_round,
}


def _binop(op: ast.operator, left: Decimal, right: Decimal) -> Decimal:
    if isinstance(op, (ast.Mod, ast.FloorDiv)):
        raise _CalcError(ERROR_UNSUPPORTED_OPERATOR, HINT_UNSUPPORTED_OPERATOR)
    if isinstance(op, ast.Add):
        return left + right
    if isinstance(op, ast.Sub):
        return left - right
    if isinstance(op, ast.Mult):
        return left * right
    if isinstance(op, ast.Div):
        if right == 0:
            raise _CalcError(ERROR_DIVISION_BY_ZERO)
        return left / right
    if isinstance(op, ast.Pow):
        if right != right.to_integral_value():
            raise _CalcError(ERROR_EXPONENT_NOT_INTEGER)
        if abs(right) > MAX_ABS_EXPONENT:
            raise _CalcError(ERROR_EXPONENT_OUT_OF_RANGE)
        if abs(left) > MAX_BASE_ABS_FOR_POW:
            raise _CalcError(ERROR_BASE_OUT_OF_RANGE)
        # P6-CALC: 0 to a negative power is division by zero — P6-D08
        if left == 0 and right < 0:
            raise _CalcError(ERROR_DIVISION_BY_ZERO)
        # P6-CALC: pre-check only when |base|>1 and exp>0; reject if estimate > 40 — P6-D08
        if abs(left) > 1 and right > 0:
            try:
                log10_base = abs(left).ln() / Decimal(10).ln()
                estimated = int(
                    (right * log10_base).to_integral_value(rounding=ROUND_FLOOR)
                ) + 1
                if estimated > MAX_RESULT_DIGITS:
                    raise _CalcError(ERROR_RESULT_TOO_LARGE)
            except _CalcError:
                raise
            except DecimalException:
                raise _CalcError(ERROR_INVALID_ARGUMENT) from None
        try:
            return left ** right
        except DecimalException:
            raise _CalcError(ERROR_INVALID_ARGUMENT) from None
    raise _CalcError(ERROR_UNSUPPORTED_NODE)


class _Evaluator:
    def __init__(self, source: str, deadline: float) -> None:
        self._source = source
        self._deadline = deadline

    def _tick(self) -> None:
        # P6-CALC: secondary wall-clock between node evaluations — P6-D08
        if time.monotonic() > self._deadline:
            raise _CalcError(ERROR_TIMEOUT)

    def eval_node(self, node: ast.AST) -> Decimal:
        self._tick()
        if isinstance(node, ast.Expression):
            return self.eval_node(node.body)
        if isinstance(node, ast.Constant):
            return _check_result_digits(_parse_literal(self._source, node))
        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in _ALLOWED_UNARY:
                raise _CalcError(ERROR_UNSUPPORTED_NODE)
            value = self.eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return _check_result_digits(value)
            return _check_result_digits(-value)
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in _REJECTED_BINOPS:
                raise _CalcError(ERROR_UNSUPPORTED_OPERATOR, HINT_UNSUPPORTED_OPERATOR)
            if op_type not in _ALLOWED_BINOPS:
                raise _CalcError(ERROR_UNSUPPORTED_NODE)
            left = self.eval_node(node.left)
            right = self.eval_node(node.right)
            try:
                result = _binop(node.op, left, right)
            except _CalcError:
                raise
            except DecimalException:
                raise _CalcError(ERROR_INVALID_ARGUMENT) from None
            return _check_result_digits(result)
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise _CalcError(ERROR_UNSUPPORTED_NODE)
            if node.keywords:
                raise _CalcError(ERROR_UNSUPPORTED_NODE)
            name = node.func.id
            fn = _FUNCTIONS.get(name)
            if fn is None:
                raise _CalcError(ERROR_UNSUPPORTED_FUNCTION)
            args = [self.eval_node(arg) for arg in node.args]
            try:
                result = fn(args)
            except _CalcError:
                raise
            except DecimalException:
                raise _CalcError(ERROR_INVALID_ARGUMENT) from None
            return _check_result_digits(result)
        if isinstance(node, ast.Name):
            raise _CalcError(ERROR_UNSUPPORTED_NAME)
        raise _CalcError(ERROR_UNSUPPORTED_NODE)


def evaluate(expression: Any) -> Dict[str, Any]:
    """Evaluate an arithmetic expression; never raises — always returns ok/error dict."""
    if not isinstance(expression, str):
        return _error_dict(ERROR_INVALID_TYPE)
    if expression.strip() == "":
        return _error_dict(ERROR_EMPTY_EXPRESSION)
    if len(expression) > MAX_INPUT_LENGTH:
        return _error_dict(ERROR_INPUT_TOO_LONG)

    try:
        tree = ast.parse(expression, mode="eval")
    except Exception:
        # P6-CALC: RecursionError/MemoryError/ValueError → syntax_error — P6-D08
        return _error_dict(ERROR_SYNTAX)

    try:
        node_count = sum(1 for _ in ast.walk(tree))
    except Exception:
        return _error_dict(ERROR_SYNTAX)
    if node_count > MAX_NODE_COUNT:
        return _error_dict(ERROR_NODE_LIMIT)

    deadline = time.monotonic() + (WALL_CLOCK_MS / 1000.0)
    ctx = Context(prec=DECIMAL_PRECISION, rounding=ROUND_HALF_UP)
    try:
        with localcontext(ctx):
            value = _Evaluator(expression, deadline).eval_node(tree)
            _check_result_digits(value)
            text = _format_result(value)
            return {"ok": True, "result": text}
    except _CalcError as exc:
        return _error_dict(exc.code, exc.hint)
    except DecimalException:
        return _error_dict(ERROR_INVALID_ARGUMENT)
    except Exception:
        # P6-CALC: no exception escapes the evaluator — P6-D08
        return _error_dict(ERROR_INVALID_ARGUMENT)


def node_count_of(expression: str) -> Optional[int]:
    """Return AST node count for diagnostics/tests, or None if parse fails."""
    try:
        tree = ast.parse(expression, mode="eval")
        return sum(1 for _ in ast.walk(tree))
    except Exception:
        return None
