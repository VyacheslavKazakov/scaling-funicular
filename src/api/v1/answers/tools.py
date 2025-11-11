import ast
import logging
from langchain_core.tools import tool
from pydantic import Field, BaseModel

from src.api.v1.answers.helpers import ALLOWED_PYTHON_MODULES, SAFE_NAMESPACE

logger = logging.getLogger(__name__)


class SafeExecuteCodeInput(BaseModel):
    code_string: str = Field(description="the code to be executed including imports")
    function_name: str = Field(description="the function to be run")
    args: list[str | int | float | bool] = Field(
        description="Arguments to pass to the function"
    )


@tool(args_schema=SafeExecuteCodeInput)
def safe_execute_code_tool(
    code_string: str,
    function_name: str,
    args: list[str | int | float | bool],
):
    """Run code string with imports and function call with arguments"""
    logger.debug(f"Executing code: {code_string}")
    logger.debug(f"Function name: {function_name}")
    logger.debug(f"Args: {args}")

    try:
        tree = ast.parse(code_string)
    except SyntaxError as e:
        logger.exception(e)
        # ToDo: request a correction in the future with this error
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in ALLOWED_PYTHON_MODULES:
                    logger.error(f"Error: module '{alias.name}' is not allowed")
                    # ToDo: request a correction in the future with this
                    return None

        if isinstance(node, ast.ImportFrom):
            if node.module not in ALLOWED_PYTHON_MODULES:
                logger.error(f"Error: module '{node.module}' is not allowed")
                # ToDo: request a correction in the future with this
                return None

    try:
        code = compile(tree, "<string>", "exec")
        local_namespace = SAFE_NAMESPACE.copy()
        exec(code, SAFE_NAMESPACE, local_namespace)

        if function_name not in local_namespace:
            logger.error(f"Error: function '{function_name}' not found")
            return None

        func = local_namespace[function_name]
        result = func(*args)
        return result
    except Exception as e:
        logger.exception(e)
        # ToDo: request a correction in the future with this error
        return None
