import os
from typing import Any, Callable, Optional, Union
from decouple import config as decouple_config


def get_env(
        name: str,
        default: Optional[Any] = None,
        cast: Union[type, Callable] = str,
        required: bool = False,
        use_decouple: bool = False
) -> Any:
    """
    Retrieve an environment variable with optional casting.
    Can optionally use python-decouple's config().

    Special support:
      - cast=bool -> converts "true", "1", "yes", "on" to True
      - cast=list -> splits string by commas and strips spaces

    :param name: Environment variable name
    :param default: Default value if the variable is not set or invalid
    :param cast: Type or callable used for casting (str, int, bool, float, list, custom func)
    :param required: If True, raises ValueError when the variable is not set
    :param use_decouple: If True, use decouple.config() to retrieve the variable
    :return: The environment variable value, cast to the specified type
    """
    value = None

    if use_decouple:
        try:
            return decouple_config(name, default=default, cast=cast)
        except Exception:
            if required:
                raise ValueError(f"Required environment variable '{name}' is not set.")
            return default
        return

    value = os.environ.get(name, None)

    if value is None:
        if required:
            raise ValueError(f"Required environment variable '{name}' is not set.")
        return default

    if cast == bool:
        return str(value).strip().lower() in ("true", "1", "yes", "y", "on")
    elif cast == list:
        return [s.strip() for s in str(value).split(",") if s.strip()]
    else:
        try:
            return cast(value)
        except (ValueError, TypeError):
            return default
