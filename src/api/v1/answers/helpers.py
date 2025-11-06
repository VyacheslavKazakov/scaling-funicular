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
        "bytes": bytes,
        "bytearray": bytearray,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "ZeroDivisionError": ZeroDivisionError,
        "IndexError": IndexError,
        "KeyError": KeyError,
        "ImportError": ImportError,
        "AttributeError": AttributeError,
        "RuntimeError": RuntimeError,
        "Exception": Exception,
        "divmod": divmod,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "hasattr": hasattr,
        "getattr": getattr,
        "setattr": setattr,
        "callable": callable,
        "__import__": safe_import,
    },
}

SAFE_NAMESPACE.update(AVAILABLE_PYTHON_MODULES)
