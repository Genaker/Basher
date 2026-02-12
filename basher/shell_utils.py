"""Shell escaping utilities for safe command construction."""

import shlex


def quote(value: str) -> str:
    """
    Safely quote a value for use in a shell command.
    Uses shlex.quote() to prevent injection.
    """
    return shlex.quote(value)
