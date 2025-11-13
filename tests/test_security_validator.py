import pytest
import ast
import textwrap
from src.api.v1.answers.helpers import (
    validate_code_security,
    SecurityViolation,
)


class TestCodeSecurityValidator:
    """Tests for AST security validator"""

    def test_dangerous_attributes_blocked(self):
        """Test that dangerous attributes are blocked"""
        dangerous_codes = [
            "x.__class__",
            "x.__bases__",
            "x.__subclasses__()",
            "x.__globals__",
            "x.__code__",
            "x.__builtins__",
            "x.__dict__",
            "x.__mro__",
            "x.__import__",
            "x.func_globals",
            "x.func_code",
            "x.gi_frame",
            "x.gi_code",
            "x.cr_frame",
            "x.cr_code",
        ]

        for code in dangerous_codes:
            with pytest.raises(SecurityViolation, match="dangerous attribute"):
                validate_code_security(code)

    def test_while_loops_blocked(self):
        """Test that while loops are blocked"""
        code = textwrap.dedent("""
        while True:
            pass
        """)
        with pytest.raises(SecurityViolation, match="While loops are not allowed"):
            validate_code_security(code)

    def test_recursion_blocked(self):
        """Test that recursion is detected and blocked"""
        code = textwrap.dedent("""
        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)
        """)
        with pytest.raises(SecurityViolation, match="Recursion detected"):
            validate_code_security(code)

    def test_excessive_function_nesting_blocked(self):
        """Test that excessive function nesting is blocked"""
        # MAX_FUNCTION_DEPTH is 2, so 3 levels should fail
        code = textwrap.dedent("""
        def outer():
            def middle():
                def inner():
                    return 42
                return inner()
            return middle()
        """)
        with pytest.raises(
            SecurityViolation, match="Function nesting depth exceeds maximum"
        ):
            validate_code_security(code)

    def test_excessive_lambda_nesting_blocked(self):
        """Test that excessive lambda nesting is blocked"""
        code = textwrap.dedent("""
        f = lambda x: (lambda y: (lambda z: z + 1)(y))(x)
        """)
        with pytest.raises(
            SecurityViolation, match="Lambda nesting depth exceeds maximum"
        ):
            validate_code_security(code)

    def test_safe_code_passes(self):
        """Test that safe code passes validation"""
        safe_codes = [
            "x = 1 + 2",
            "def add(a, b): return a + b",
            "import math\nresult = math.sqrt(16)",
            "for i in range(10): pass",
            "[x * 2 for x in range(10)]",
            "lambda x: x + 1",
            "def outer():\n    def inner():\n        return 42\n    return inner()",
        ]

        for code in safe_codes:
            try:
                tree = validate_code_security(code)
                assert isinstance(tree, ast.AST)
            except SecurityViolation as e:
                pytest.fail(f"Safe code was blocked: {code}\nError: {e}")

    def test_comprehensions_allowed(self):
        """Test that comprehensions are allowed"""
        comprehension_codes = [
            "[x * 2 for x in range(10)]",
            "{x: x * 2 for x in range(10)}",
            "{x * 2 for x in range(10)}",
            "(x * 2 for x in range(10))",
        ]

        for code in comprehension_codes:
            try:
                tree = validate_code_security(code)
                assert isinstance(tree, ast.AST)
            except SecurityViolation as e:
                pytest.fail(f"Comprehension was blocked: {code}\nError: {e}")

    def test_for_loops_allowed(self):
        """Test that for loops are allowed (only while is blocked)"""
        code = textwrap.dedent("""
        def sum_range(n):
            total = 0
            for i in range(n):
                total += i
            return total
        """)
        try:
            tree = validate_code_security(code)
            assert isinstance(tree, ast.AST)
        except SecurityViolation as e:
            pytest.fail(f"For loop was incorrectly blocked: {e}")

    def test_nested_function_within_limit(self):
        """Test that nested functions within limit are allowed"""
        # MAX_FUNCTION_DEPTH is 2, so 2 levels should pass
        code = textwrap.dedent("""
        def outer():
            def inner():
                return 42
            return inner()
        """)
        try:
            tree = validate_code_security(code)
            assert isinstance(tree, ast.AST)
        except SecurityViolation as e:
            pytest.fail(f"Safe nested function was blocked: {e}")

    def test_non_recursive_function_calls_allowed(self):
        """Test that non-recursive function calls are allowed"""
        code = textwrap.dedent("""
        def helper(x):
            return x * 2

        def main(x):
            return helper(x) + 1
        """)
        try:
            tree = validate_code_security(code)
            assert isinstance(tree, ast.AST)
        except SecurityViolation as e:
            pytest.fail(f"Non-recursive function call was blocked: {e}")

    def test_indirect_recursion_not_detected(self):
        """Test that indirect recursion is NOT detected (known limitation)"""
        # This is a known limitation - we only detect direct recursion
        code = textwrap.dedent("""
        def func_a(n):
            if n <= 0:
                return 1
            return func_b(n - 1)

        def func_b(n):
            return func_a(n - 1)
        """)
        # This should pass validation (indirect recursion not detected by current validator)
        tree = validate_code_security(code)
        assert isinstance(tree, ast.AST)

    def test_syntax_error_propagates(self):
        """Test that syntax errors are propagated"""
        code = "def invalid syntax here"
        with pytest.raises(SyntaxError):
            validate_code_security(code)
