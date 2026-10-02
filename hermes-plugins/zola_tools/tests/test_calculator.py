"""Unit tests for zola_tools.calculator (synthetic expressions only) — P6-D08."""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import time
import unittest
from decimal import InvalidOperation
from pathlib import Path
from unittest import mock

from calculator import (
    DECIMAL_PRECISION,
    ERROR_DIVISION_BY_ZERO,
    ERROR_EXPONENT_OUT_OF_RANGE,
    ERROR_INPUT_TOO_LONG,
    ERROR_INVALID_ARGUMENT,
    ERROR_INVALID_LITERAL,
    ERROR_INVALID_TYPE,
    ERROR_NEGATIVE_SQRT,
    ERROR_NODE_LIMIT,
    ERROR_RESULT_TOO_LARGE,
    ERROR_RESULT_TOO_SMALL,
    ERROR_UNSUPPORTED_FUNCTION,
    ERROR_UNSUPPORTED_NAME,
    ERROR_UNSUPPORTED_NODE,
    ERROR_UNSUPPORTED_OPERATOR,
    HINT_UNSUPPORTED_OPERATOR,
    MAX_ABS_EXPONENT,
    MAX_BASE_ABS_FOR_POW,
    MAX_INPUT_LENGTH,
    MAX_NODE_COUNT,
    MAX_OUTPUT_DECIMALS,
    MAX_RESULT_DIGITS,
    WALL_CLOCK_MS,
    evaluate,
)


def _ok(expression: str) -> str:
    result = evaluate(expression)
    assert result.get("ok") is True, result
    return result["result"]


def _err(expression) -> str:
    result = evaluate(expression)
    assert result.get("ok") is False, result
    return result["error"]


def _fail(expression) -> dict:
    result = evaluate(expression)
    assert result.get("ok") is False, result
    return result


def _load_plugin_module(hermes_home: str):
    """Load __init__.py as a module with HERMES_HOME pointed at a temp profile."""
    init_path = Path(__file__).resolve().parents[1] / "__init__.py"
    env = {**os.environ, "HERMES_HOME": hermes_home}
    with mock.patch.dict(os.environ, env, clear=False):
        spec = importlib.util.spec_from_file_location("zola_tools_plugin_under_test", init_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module


class TestP4Cases(unittest.TestCase):
    def test_17_times_23(self):
        self.assertEqual(_ok("17*23"), "391")

    def test_percent_style(self):
        self.assertEqual(_ok("0.15*240"), "36")

    def test_money_sum(self):
        self.assertEqual(_ok("1347.12+466.72+565"), "2378.84")


class TestArithmeticBasics(unittest.TestCase):
    def test_precedence_and_parens(self):
        self.assertEqual(_ok("2+3*4"), "14")
        self.assertEqual(_ok("(2+3)*4"), "20")

    def test_unary_minus(self):
        self.assertEqual(_ok("-3+5"), "2")
        self.assertEqual(_ok("-(2+3)"), "-5")

    def test_division_by_zero(self):
        self.assertEqual(_err("1/0"), ERROR_DIVISION_BY_ZERO)

    def test_decimal_exactness(self):
        self.assertEqual(_ok("0.1+0.2"), "0.3")

    def test_thirty_five_digit_product_exact(self):
        # P6-CALC: 35-digit integer product exact under prec=50 — P6-D08
        factor = "11111111111111111111111111111111111"
        self.assertEqual(len(factor), 35)
        self.assertEqual(_ok(f"{factor}*1"), factor)
        self.assertEqual(DECIMAL_PRECISION, 50)
        self.assertEqual(MAX_RESULT_DIGITS, 40)


class TestRejectedConstructs(unittest.TestCase):
    def test_import_call(self):
        self.assertEqual(_err("__import__('os').system('x')"), ERROR_UNSUPPORTED_NODE)

    def test_attribute_access(self):
        self.assertEqual(_err("(1).real"), ERROR_UNSUPPORTED_NODE)

    def test_bare_name(self):
        self.assertEqual(_err("os"), ERROR_UNSUPPORTED_NAME)

    def test_lambda(self):
        self.assertEqual(_err("(lambda: 1)()"), ERROR_UNSUPPORTED_NODE)

    def test_string(self):
        self.assertEqual(_err("'hi'"), ERROR_INVALID_LITERAL)

    def test_fstring(self):
        # f-strings are JoinedStr / FormattedValue in the AST.
        self.assertEqual(_err("f'1'"), ERROR_UNSUPPORTED_NODE)

    def test_subscript(self):
        self.assertEqual(_err("[1][0]"), ERROR_UNSUPPORTED_NODE)

    def test_comprehension(self):
        self.assertEqual(_err("[x for x in [1]]"), ERROR_UNSUPPORTED_NODE)

    def test_call_outside_allowlist(self):
        self.assertEqual(_err("pow(2, 3)"), ERROR_UNSUPPORTED_FUNCTION)

    def test_huge_power(self):
        err = _err("9**9**9")
        self.assertIn(err, (ERROR_EXPONENT_OUT_OF_RANGE, ERROR_RESULT_TOO_LARGE))

    def test_deep_nesting_bomb(self):
        # Parentheses alone are not AST nodes; nest allowlisted calls past MAX_NODE_COUNT.
        depth = 70
        expr = ("abs(" * depth) + "1" + (")" * depth)
        self.assertEqual(_err(expr), ERROR_NODE_LIMIT)

    def test_oversize_input(self):
        self.assertEqual(_err("1+" + ("1" * MAX_INPUT_LENGTH)), ERROR_INPUT_TOO_LONG)

    def test_result_over_digit_limit(self):
        big = "1" + ("0" * 40)
        self.assertEqual(len(big), 41)
        self.assertEqual(_err(big), ERROR_RESULT_TOO_LARGE)


class TestUnsupportedOperators(unittest.TestCase):
    def test_modulo_rejected_with_hint(self):
        payload = _fail("10%3")
        self.assertEqual(payload["error"], ERROR_UNSUPPORTED_OPERATOR)
        self.assertEqual(payload.get("hint"), HINT_UNSUPPORTED_OPERATOR)

    def test_floordiv_rejected_with_hint(self):
        payload = _fail("10//3")
        self.assertEqual(payload["error"], ERROR_UNSUPPORTED_OPERATOR)
        self.assertEqual(payload.get("hint"), HINT_UNSUPPORTED_OPERATOR)


class TestInvalidLiterals(unittest.TestCase):
    def test_hex(self):
        self.assertEqual(_err("0x10"), ERROR_INVALID_LITERAL)

    def test_binary(self):
        self.assertEqual(_err("0b101"), ERROR_INVALID_LITERAL)

    def test_octal(self):
        self.assertEqual(_err("0o7"), ERROR_INVALID_LITERAL)

    def test_imaginary(self):
        self.assertEqual(_err("1j"), ERROR_INVALID_LITERAL)

    def test_underscore(self):
        self.assertEqual(_err("1_000"), ERROR_INVALID_LITERAL)

    def test_allowed_literal_forms(self):
        self.assertEqual(_ok("12"), "12")
        self.assertEqual(_ok("0.5"), "0.5")
        self.assertEqual(_ok(".5"), "0.5")
        self.assertEqual(_ok("1e3"), "1000")
        self.assertEqual(_ok("2.5E-4"), "0.00025")


class TestFunctions(unittest.TestCase):
    def test_round_half_up(self):
        self.assertEqual(_ok("round(2.5)"), "3")
        self.assertEqual(_ok("round(1.235, 2)"), "1.24")

    def test_sqrt_negative(self):
        self.assertEqual(_err("sqrt(-1)"), ERROR_NEGATIVE_SQRT)

    def test_floor_ceil_negatives(self):
        self.assertEqual(_ok("floor(-3.5)"), "-4")
        self.assertEqual(_ok("ceil(-3.5)"), "-3")

    def test_abs_min_max(self):
        self.assertEqual(_ok("abs(-7)"), "7")
        self.assertEqual(_ok("min(3, 1, 2)"), "1")
        self.assertEqual(_ok("max(3, 1, 2)"), "3")

    def test_zero_to_negative_power(self):
        self.assertEqual(_err("0**-1"), ERROR_DIVISION_BY_ZERO)


class TestBoundsAndGuard(unittest.TestCase):
    def test_worst_case_allowed_under_wall_clock(self):
        # Near-bound allowed input: max base**6 (37 digits) plus a long sum under node/input caps.
        parts = ["1"]
        while True:
            trial = parts + ["1"]
            expr = "+".join(trial)
            # Leave headroom for wrapping + power term nodes.
            if len(expr) > MAX_INPUT_LENGTH - 80:
                break
            if 3 * len(trial) + 20 > MAX_NODE_COUNT:
                break
            parts = trial
        bound_expr = f"{'+'.join(parts)}+{MAX_BASE_ABS_FOR_POW}**6"
        self.assertLessEqual(len(bound_expr), MAX_INPUT_LENGTH)
        started = time.perf_counter()
        result = evaluate(bound_expr)
        elapsed_ms = (time.perf_counter() - started) * 1000
        self.assertTrue(result.get("ok"), result)
        self.assertLess(elapsed_ms, WALL_CLOCK_MS)
        print(f"worst_case_allowed_ms={elapsed_ms:.3f}")
        self.assertEqual(MAX_ABS_EXPONENT, 1000)
        self.assertEqual(MAX_NODE_COUNT, 128)


class TestHandlerContract(unittest.TestCase):
    def test_handler_never_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = _load_plugin_module(tmp)
            for bad in ("", None, 123, {}, []):
                raw = plugin.calculate_handler({"expression": bad})
                payload = json.loads(raw)
                self.assertIsInstance(payload, dict)
                self.assertFalse(payload.get("ok"))
            raw = plugin.calculate_handler("not-a-dict")
            payload = json.loads(raw)
            self.assertFalse(payload.get("ok"))
            self.assertEqual(payload.get("error"), ERROR_INVALID_TYPE)

    def test_decimal_exception_mapped(self):
        import calculator as calc_mod

        original = calc_mod._FUNCTIONS["sqrt"]

        def boom(_args):
            raise InvalidOperation()

        calc_mod._FUNCTIONS["sqrt"] = boom
        try:
            self.assertEqual(_err("sqrt(4)"), ERROR_INVALID_ARGUMENT)
        finally:
            calc_mod._FUNCTIONS["sqrt"] = original

    def test_evaluate_never_raises_on_malformed(self):
        for bad in ("", None, 123, {}, []):
            result = evaluate(bad)
            self.assertFalse(result.get("ok"))
            self.assertIn("error", result)


class TestPhase3bOutputAndDigits(unittest.TestCase):
    def test_repeating_and_roots_rounded_to_15(self):
        self.assertEqual(MAX_OUTPUT_DECIMALS, 15)
        self.assertEqual(_ok("10/3"), "3.333333333333333")
        self.assertEqual(_ok("100/7"), "14.285714285714286")
        self.assertEqual(_ok("sqrt(2)"), "1.414213562373095")
        self.assertEqual(_ok("1/8"), "0.125")

    def test_power_integer_digit_bounds(self):
        # 10**39 → 40 integer digits (allowed); 10**40 rejected.
        self.assertEqual(_ok("10**39"), "1" + ("0" * 39))
        self.assertEqual(_err("10**40"), ERROR_RESULT_TOO_LARGE)

    def test_result_too_small(self):
        self.assertEqual(_err("1e-20*1"), ERROR_RESULT_TOO_SMALL)

    def test_negative_exponent_rounded(self):
        self.assertEqual(_ok("2**-30"), "0.000000000931323")


class TestPhase3bHandlerRobustness(unittest.TestCase):
    def test_huge_input_input_too_long_no_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = _load_plugin_module(tmp)
            huge = "1+" + ("1" * 1_200_000)
            raw = plugin.calculate_handler({"expression": huge})
            payload = json.loads(raw)
            self.assertFalse(payload.get("ok"))
            self.assertEqual(payload.get("error"), ERROR_INPUT_TOO_LONG)

    def test_max_length_deep_nest_no_raise(self):
        # 500-char deeply nested abs(...) — may hit node_limit/syntax; must not raise.
        depth = 80
        inner = ("abs(" * depth) + "1" + (")" * depth)
        expr = inner[:MAX_INPUT_LENGTH]
        result = evaluate(expr)
        self.assertIsInstance(result.get("ok"), bool)
        with tempfile.TemporaryDirectory() as tmp:
            plugin = _load_plugin_module(tmp)
            raw = plugin.calculate_handler({"expression": expr})
            payload = json.loads(raw)
            self.assertIsInstance(payload.get("ok"), bool)


if __name__ == "__main__":
    unittest.main()

