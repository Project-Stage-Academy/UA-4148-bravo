import os
from typing import Any, Callable, Optional, Union
from dotenv import load_dotenv

load_dotenv()


def get_env(
        name: str,
        default: Optional[Any] = None,
        cast: Union[type, Callable] = str,
        required: bool = False
) -> Any:
    """
    Retrieve an environment variable with optional casting.

    :param name: Environment variable name
    :param default: Default value if the variable is not set or invalid
    :param cast: Type or callable used for casting (str, int, bool, float, list, custom func)
    :param required: If True, raises ValueError when the variable is not set
    :return: The environment variable value, cast to the specified type
    """
    value = os.environ.get(name, None)

    if value is None:
        if required:
            raise ValueError(f"Required environment variable '{name}' is not set.")
        return default

    if cast == bool:
        return str(value).lower() in ("true", "1", "yes", "y", "on")

    try:
        return cast(value)
    except (ValueError, TypeError):
        return default
