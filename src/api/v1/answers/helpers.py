import ast
import math
import cmath
import fractions
import decimal
import itertools
import functools
import random
import statistics
import operator as op
from typing import Any

ALLOWED_PYTHON_MODULES = frozenset(
    {
        "math",
        "cmath",
        "fractions",
        "decimal",
        "itertools",
        "functools",
        "operator",
        "statistics",
        "random",
    }
)


AVAILABLE_PYTHON_MODULES = {
    "math": math,
    "cmath": cmath,
    "fractions": fractions,
    "decimal": decimal,
    "itertools": itertools,
    "functools": functools,
    "operator": op,
    "statistics": statistics,
    "random": random,
}


def safe_import(name, globals_dict=None, locals_dict=None, fromlist=(), level=0):
    if name not in ALLOWED_PYTHON_MODULES:
        raise ImportError(f"Import of module '{name}' is not allowed")

    module = AVAILABLE_PYTHON_MODULES.get(name)
    if module is None:
        module = __import__(name, globals_dict, locals_dict, fromlist, level)

    return module


class SecurityViolation(Exception):
    pass


class CodeSecurityValidator(ast.NodeVisitor):
    """
    Validates AST for security violations:
    - Dangerous attribute access (__class__, __bases__, __subclasses__, __globals__, etc.)
    - While loops (potential infinite loops)
    - Excessive function nesting
    - Recursion
    - Dangerous node types (Exec, Eval, etc.)
    """

    DANGEROUS_ATTRIBUTES = frozenset(
        {
            "__class__",
            "__bases__",
            "__subclasses__",
            "__globals__",
            "__code__",
            "__builtins__",
            "__dict__",
            "__mro__",
            "__import__",
            "func_globals",
            "func_code",
            "gi_frame",
            "gi_code",
            "cr_frame",
            "cr_code",
        }
    )

    MAX_FUNCTION_DEPTH = 2

    def __init__(self):
        self.function_depth = 0
        self.function_names = set()
        self.current_function = None

    def validate(self, tree: ast.AST) -> None:
        self.visit(tree)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in self.DANGEROUS_ATTRIBUTES:
            raise SecurityViolation(
                f"Access to dangerous attribute '{node.attr}' is not allowed"
            )
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        raise SecurityViolation("While loops are not allowed (potential infinite loop)")

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.function_depth += 1

        if self.function_depth > self.MAX_FUNCTION_DEPTH:
            raise SecurityViolation(
                f"Function nesting depth exceeds maximum ({self.MAX_FUNCTION_DEPTH})"
            )

        previous_function = self.current_function
        self.current_function = node.name
        self.function_names.add(node.name)

        self.generic_visit(node)

        self.current_function = previous_function
        self.function_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            if node.func.id == self.current_function:
                raise SecurityViolation(
                    f"Recursion detected: function '{self.current_function}' calls itself"
                )
        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self.function_depth += 1

        if self.function_depth > self.MAX_FUNCTION_DEPTH:
            raise SecurityViolation(
                f"Lambda nesting depth exceeds maximum ({self.MAX_FUNCTION_DEPTH})"
            )

        self.generic_visit(node)
        self.function_depth -= 1

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self.generic_visit(node)


def validate_code_security(code_string: str) -> ast.AST:
    tree = ast.parse(code_string)
    validator = CodeSecurityValidator()
    validator.validate(tree)
    return tree


SAFE_NAMESPACE: dict[str, Any] = {
    "__builtins__": {
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "sum": sum,
        "abs": abs,
        "min": min,
        "max": max,
        "pow": pow,
        "round": round,
        "sorted": sorted,
        "reversed": reversed,
        "all": all,
        "any": any,
        "int": int,
        "float": float,
        "complex": complex,
        "str": str,
        "list": list,
        "tuple": tuple,
        "dict": dict,
        "set": set,
        "frozenset": frozenset,
        "bool": bool,
        "divmod": divmod,
        "isinstance": isinstance,
        "__import__": safe_import,
    },
}

SAFE_NAMESPACE.update(AVAILABLE_PYTHON_MODULES)
