"""Secret and confirmation input helpers for operational scripts."""

from __future__ import annotations

import getpass
import hmac
import os
import sys


MIN_ADMIN_PASSWORD_LENGTH = 12


def _secrets_match(left: str, right: str) -> bool:
    """Compare arbitrary Unicode input without leaking early mismatch timing."""
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def _validate_secret(value: str, *, env_name: str, min_length: int) -> str:
    if not value:
        raise RuntimeError(f"{env_name} must not be empty")
    if len(value) < min_length:
        raise RuntimeError(
            f"{env_name} must contain at least {min_length} characters"
        )
    return value


def read_secret(
    env_name: str,
    *,
    prompt: str,
    confirmation_prompt: str | None = None,
    min_length: int = MIN_ADMIN_PASSWORD_LENGTH,
) -> str:
    """Read a secret from the environment or a hidden interactive prompt."""
    environment_value = os.environ.get(env_name)
    if environment_value is not None:
        return _validate_secret(
            environment_value,
            env_name=env_name,
            min_length=min_length,
        )

    if not sys.stdin.isatty():
        raise RuntimeError(
            f"{env_name} must be set when this script runs non-interactively"
        )

    value = _validate_secret(
        getpass.getpass(prompt),
        env_name=env_name,
        min_length=min_length,
    )
    if confirmation_prompt is not None:
        confirmation = getpass.getpass(confirmation_prompt)
        if not _secrets_match(value, confirmation):
            raise RuntimeError("Secret confirmation did not match")
    return value


def require_confirmation(
    env_name: str,
    *,
    expected: str,
    prompt: str,
) -> None:
    """Require an exact environment or interactive confirmation phrase."""
    supplied = os.environ.get(env_name)
    if supplied is None:
        if not sys.stdin.isatty():
            raise RuntimeError(
                f"{env_name}={expected} is required for non-interactive use"
            )
        supplied = input(prompt)

    if not _secrets_match(supplied.strip(), expected):
        raise RuntimeError("Confirmation phrase did not match; operation cancelled")
