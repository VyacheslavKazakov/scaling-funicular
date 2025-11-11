import pytest
import textwrap
from unittest.mock import patch
from src.api.v1.answers.tools import safe_execute_code_tool


class TestSafeExecuteCodeTool:
    """Tests for safe_execute_code_tool"""

    @pytest.mark.asyncio
    async def test_simple_math_execution(self):
        """Test execution of simple math function"""
        code = textwrap.dedent("""
        def add(a, b):
            return a + b
        """)
        result = await safe_execute_code_tool.ainvoke(
            {"code_string": code, "function_name": "add", "args": [5, 3]}
        )
        assert result == 8

    @pytest.mark.asyncio
    async def test_execution_with_imports(self):
        """Test execution with allowed imports"""
        code = textwrap.dedent("""
        import math

        def calculate_sqrt(x):
            return math.sqrt(x)
        """)
        result = await safe_execute_code_tool.ainvoke(
            {"code_string": code, "function_name": "calculate_sqrt", "args": [16]}
        )
        assert result == 4.0

    @pytest.mark.asyncio
    async def test_execution_with_multiple_allowed_modules(self):
        """Test execution with multiple allowed modules"""
        code = textwrap.dedent("""
        import math
        import statistics

        def calculate_mean_and_sqrt(a, b, c):
            mean = statistics.mean([a, b, c])
            return math.sqrt(mean)
        """)
        result = await safe_execute_code_tool.ainvoke(
            {
                "code_string": code,
                "function_name": "calculate_mean_and_sqrt",
                "args": [1, 4, 9],
            }
        )
        # mean([1, 4, 9]) = 14/3 = 4.666..., sqrt(4.666...) = 2.16
        assert result == pytest.approx(2.16, rel=0.01)

    @pytest.mark.asyncio
    async def test_blocked_dangerous_import(self):
        """Test that dangerous imports are blocked"""
        dangerous_imports = [
            "import os",
            "import sys",
            "import subprocess",
            "import socket",
            "from os import system",
        ]

        for code in dangerous_imports:
            code_with_func = textwrap.dedent(f"""
            {code}

            def dangerous_func():
                return "should not execute"
            """)
            result = await safe_execute_code_tool.ainvoke(
                {
                    "code_string": code_with_func,
                    "function_name": "dangerous_func",
                    "args": [],
                }
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_blocked_dangerous_attribute_access(self):
        """Test that dangerous attribute access is blocked"""
        code = textwrap.dedent("""
        def exploit():
            return ().__class__.__bases__[0].__subclasses__()
        """)
        result = await safe_execute_code_tool.ainvoke(
            {"code_string": code, "function_name": "exploit", "args": []}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_blocked_while_loop(self):
        """Test that while loops are blocked"""
        code = textwrap.dedent("""
        def infinite_loop():
            while True:
                pass
            return 1
        """)
        result = await safe_execute_code_tool.ainvoke(
            {"code_string": code, "function_name": "infinite_loop", "args": []}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_blocked_recursion(self):
        """Test that recursion is blocked"""
        code = textwrap.dedent("""
        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)
        """)
        result = await safe_execute_code_tool.ainvoke(
            {"code_string": code, "function_name": "factorial", "args": [5]}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_syntax_error_handling(self):
        """Test handling of syntax errors"""
        code = "def invalid syntax here"
        result = await safe_execute_code_tool.ainvoke(
            {"code_string": code, "function_name": "invalid", "args": []}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_function_not_found(self):
        """Test handling when function is not found"""
        code = textwrap.dedent("""
        def foo():
            return 42
        """)
        result = await safe_execute_code_tool.ainvoke(
            {"code_string": code, "function_name": "bar", "args": []}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_runtime_error_handling(self):
        """Test handling of runtime errors"""
        code = textwrap.dedent("""
        def divide_by_zero():
            return 1 / 0
        """)
        result = await safe_execute_code_tool.ainvoke(
            {"code_string": code, "function_name": "divide_by_zero", "args": []}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_namespace_isolation(self):
        """Test that namespace is isolated between executions"""
        code1 = textwrap.dedent("""
        def set_global():
            global test_var
            test_var = 42
            return test_var
        """)
        code2 = textwrap.dedent("""
        def get_global():
            return test_var
        """)

        # First execution sets a global
        result1 = await safe_execute_code_tool.ainvoke(
            {"code_string": code1, "function_name": "set_global", "args": []}
        )
        assert result1 == 42

        # Second execution should not see the global from first execution
        result2 = await safe_execute_code_tool.ainvoke(
            {"code_string": code2, "function_name": "get_global", "args": []}
        )
        assert result2 is None  # Should fail because test_var is not defined

    @pytest.mark.asyncio
    async def test_allowed_builtins(self):
        """Test that allowed builtins work correctly"""
        code = textwrap.dedent("""
        def use_builtins(a, b, c, d, e):
            numbers = [a, b, c, d, e]
            return sum(numbers) / len(numbers)
        """)
        result = await safe_execute_code_tool.ainvoke(
            {
                "code_string": code,
                "function_name": "use_builtins",
                "args": [1, 2, 3, 4, 5],
            }
        )
        assert result == 3.0

    @pytest.mark.asyncio
    async def test_list_comprehension(self):
        """Test that list comprehensions work"""
        code = textwrap.dedent("""
        def double_list(a, b, c):
            numbers = [a, b, c]
            return [x * 2 for x in numbers]
        """)
        result = await safe_execute_code_tool.ainvoke(
            {"code_string": code, "function_name": "double_list", "args": [1, 2, 3]}
        )
        assert result == [2, 4, 6]

    @pytest.mark.asyncio
    async def test_for_loop_allowed(self):
        """Test that for loops are allowed"""
        code = textwrap.dedent("""
        def sum_range(n):
            total = 0
            for i in range(n):
                total += i
            return total
        """)
        result = await safe_execute_code_tool.ainvoke(
            {"code_string": code, "function_name": "sum_range", "args": [10]}
        )
        assert result == 45

    @pytest.mark.asyncio
    async def test_complex_math_calculation(self):
        """Test complex mathematical calculation"""
        code = textwrap.dedent("""
        import math

        def calculate_distance(x1, y1, x2, y2):
            dx = x2 - x1
            dy = y2 - y1
            return math.sqrt(dx * dx + dy * dy)
        """)
        result = await safe_execute_code_tool.ainvoke(
            {
                "code_string": code,
                "function_name": "calculate_distance",
                "args": [0, 0, 3, 4],
            }
        )
        assert result == 5.0

    @pytest.mark.asyncio
    async def test_statistics_module(self):
        """Test statistics module usage"""
        code = textwrap.dedent("""
        import statistics

        def calculate_stats(a, b, c, d, e):
            numbers = [a, b, c, d, e]
            return {
                'mean': statistics.mean(numbers),
                'median': statistics.median(numbers),
                'stdev': statistics.stdev(numbers)
            }
        """)
        result = await safe_execute_code_tool.ainvoke(
            {
                "code_string": code,
                "function_name": "calculate_stats",
                "args": [1, 2, 3, 4, 5],
            }
        )
        assert result["mean"] == 3.0
        assert result["median"] == 3.0
        assert result["stdev"] == pytest.approx(1.58, rel=0.01)

    @pytest.mark.asyncio
    async def test_fractions_module(self):
        """Test fractions module usage"""
        code = textwrap.dedent("""
        import fractions

        def add_fractions(a, b, c, d):
            f1 = fractions.Fraction(a, b)
            f2 = fractions.Fraction(c, d)
            result = f1 + f2
            return float(result)
        """)
        result = await safe_execute_code_tool.ainvoke(
            {
                "code_string": code,
                "function_name": "add_fractions",
                "args": [1, 2, 1, 3],
            }
        )
        assert result == pytest.approx(5 / 6, rel=1e-9)

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that long-running code times out"""
        code = textwrap.dedent("""
        def long_running():
            total = 0
            for i in range(100000000):
                total += i
            return total
        """)
        with patch("src.core.config.settings.safe_execute_code_timeout_sec", 0.1):
            result = await safe_execute_code_tool.ainvoke(
                {"code_string": code, "function_name": "long_running", "args": []}
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_nested_function_within_limit(self):
        """Test nested functions within depth limit"""
        code = textwrap.dedent("""
        def outer(x):
            def inner(y):
                return y * 2
            return inner(x) + 1
        """)
        result = await safe_execute_code_tool.ainvoke(
            {"code_string": code, "function_name": "outer", "args": [5]}
        )
        assert result == 11

    @pytest.mark.asyncio
    async def test_lambda_function(self):
        """Test lambda function usage"""
        code = textwrap.dedent("""
        def apply_lambda(a, b, c):
            numbers = [a, b, c]
            double = lambda x: x * 2
            return list(map(double, numbers))
        """)
        result = await safe_execute_code_tool.ainvoke(
            {"code_string": code, "function_name": "apply_lambda", "args": [1, 2, 3]}
        )
        assert result == [2, 4, 6]

    @pytest.mark.asyncio
    async def test_different_argument_types(self):
        """Test function with different argument types"""
        code = textwrap.dedent("""
        def process_args(string, integer, floating, boolean):
            result = f"{string}_{integer}_{floating}_{boolean}"
            return result
        """)
        result = await safe_execute_code_tool.ainvoke(
            {
                "code_string": code,
                "function_name": "process_args",
                "args": ["test", 42, 3.14, True],
            }
        )
        assert result == "test_42_3.14_True"
