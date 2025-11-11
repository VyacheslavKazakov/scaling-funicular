import ast
import asyncio
import logging
from typing import Any, cast
from langchain_core.tools import tool
from pydantic import Field, BaseModel

from src.api.v1.answers.helpers import (
    ALLOWED_PYTHON_MODULES,
    SAFE_NAMESPACE,
    SecurityViolation,
    validate_code_security,
)
from src.core.config import settings

logger = logging.getLogger(__name__)


class SafeExecuteCodeInput(BaseModel):
    code_string: str = Field(description="the code to be executed including imports")
    function_name: str = Field(description="the function to be run")
    args: list[str | int | float | bool] = Field(
        description="Arguments to pass to the function"
    )


@tool(args_schema=SafeExecuteCodeInput)
async def safe_execute_code_tool(
    code_string: str,
    function_name: str,
    args: list[str | int | float | bool],
):
    """Run code string with imports and function call with arguments"""
    logger.debug(f"Executing code: {code_string}")
    logger.debug(f"Function name: {function_name}")
    logger.debug(f"Args: {args}")

    # Code validation
    try:
        tree = validate_code_security(code_string)
    except SyntaxError as e:
        logger.error(f"Syntax error in code: {e}")
        return None
    except SecurityViolation as e:
        logger.error(f"Security violation: {e}")
        return None

    # Check imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in ALLOWED_PYTHON_MODULES:
                    logger.error(f"Error: module '{alias.name}' is not allowed")
                    return None

        if isinstance(node, ast.ImportFrom):
            if node.module not in ALLOWED_PYTHON_MODULES:
                logger.error(f"Error: module '{node.module}' is not allowed")
                return None

    # Run the code in the sandbox environment
    try:
        # Cast AST to Module for mypy (ast.parse always returns Module for mode='exec')
        code = compile(cast(ast.Module, tree), "<string>", "exec")
        safe_globals = SAFE_NAMESPACE.copy()
        safe_globals["__builtins__"] = SAFE_NAMESPACE["__builtins__"].copy()
        local_namespace: dict[str, Any] = {}
        exec(code, safe_globals, local_namespace)

        if function_name not in local_namespace:
            logger.error(f"Error: function '{function_name}' not found")
            return None

        func = local_namespace[function_name]
        result = await asyncio.wait_for(
            asyncio.to_thread(func, *args), settings.safe_execute_code_timeout_sec
        )
        return result
    except Exception as e:
        logger.exception(e)
        # ToDo: request a correction in the future with this error
        return None
