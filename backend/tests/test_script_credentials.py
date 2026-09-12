"""Security regression tests for operational script credentials."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.scripts import secure_inputs
from app.scripts import test_login as login_script


class _InteractiveInput:
    def isatty(self) -> bool:
        return True


class _NonInteractiveInput:
    def isatty(self) -> bool:
        return False


def test_read_secret_prefers_environment_without_prompting(monkeypatch):
    monkeypatch.setenv("IBOOKS_ADMIN_PASSWORD", "environment-only-password")
    monkeypatch.setattr(
        secure_inputs.getpass,
        "getpass",
        lambda prompt: pytest.fail(f"unexpected prompt: {prompt}"),
    )

    assert (
        secure_inputs.read_secret(
            "IBOOKS_ADMIN_PASSWORD",
            prompt="Password: ",
            confirmation_prompt="Confirm: ",
        )
        == "environment-only-password"
    )


def test_read_secret_requires_environment_for_non_interactive_use(monkeypatch):
    monkeypatch.delenv("IBOOKS_ADMIN_PASSWORD", raising=False)
    monkeypatch.setattr(secure_inputs.sys, "stdin", _NonInteractiveInput())

    with pytest.raises(RuntimeError, match="must be set"):
        secure_inputs.read_secret(
            "IBOOKS_ADMIN_PASSWORD",
            prompt="Password: ",
        )


def test_read_secret_uses_hidden_confirmed_prompt(monkeypatch):
    monkeypatch.delenv("IBOOKS_ADMIN_PASSWORD", raising=False)
    monkeypatch.setattr(secure_inputs.sys, "stdin", _InteractiveInput())
    responses = iter(["interactive-password", "interactive-password"])
    monkeypatch.setattr(
        secure_inputs.getpass,
        "getpass",
        lambda prompt: next(responses),
    )

    assert (
        secure_inputs.read_secret(
            "IBOOKS_ADMIN_PASSWORD",
            prompt="Password: ",
            confirmation_prompt="Confirm: ",
        )
        == "interactive-password"
    )


def test_read_secret_supports_unicode_confirmation(monkeypatch):
    password = "管理员安全密码一二三四五六七八"
    monkeypatch.delenv("IBOOKS_ADMIN_PASSWORD", raising=False)
    monkeypatch.setattr(secure_inputs.sys, "stdin", _InteractiveInput())
    responses = iter([password, password])
    monkeypatch.setattr(
        secure_inputs.getpass,
        "getpass",
        lambda prompt: next(responses),
    )

    assert (
        secure_inputs.read_secret(
            "IBOOKS_ADMIN_PASSWORD",
            prompt="Password: ",
            confirmation_prompt="Confirm: ",
        )
        == password
    )


def test_read_secret_rejects_short_or_mismatched_values(monkeypatch):
    monkeypatch.setenv("IBOOKS_ADMIN_PASSWORD", "too-short")
    with pytest.raises(RuntimeError, match="at least 12"):
        secure_inputs.read_secret(
            "IBOOKS_ADMIN_PASSWORD",
            prompt="Password: ",
        )

    monkeypatch.delenv("IBOOKS_ADMIN_PASSWORD")
    monkeypatch.setattr(secure_inputs.sys, "stdin", _InteractiveInput())
    responses = iter(["first-password", "second-password"])
    monkeypatch.setattr(
        secure_inputs.getpass,
        "getpass",
        lambda prompt: next(responses),
    )
    with pytest.raises(RuntimeError, match="did not match"):
        secure_inputs.read_secret(
            "IBOOKS_ADMIN_PASSWORD",
            prompt="Password: ",
            confirmation_prompt="Confirm: ",
        )


def test_require_confirmation_accepts_only_exact_phrase(monkeypatch):
    monkeypatch.setenv("IBOOKS_ADMIN_RECREATE_CONFIRM", "wrong")
    with pytest.raises(RuntimeError, match="cancelled"):
        secure_inputs.require_confirmation(
            "IBOOKS_ADMIN_RECREATE_CONFIRM",
            expected="RECREATE_ADMIN",
            prompt="Confirm: ",
        )

    monkeypatch.setenv("IBOOKS_ADMIN_RECREATE_CONFIRM", "RECREATE_ADMIN")
    secure_inputs.require_confirmation(
        "IBOOKS_ADMIN_RECREATE_CONFIRM",
        expected="RECREATE_ADMIN",
        prompt="Confirm: ",
    )


def test_login_script_never_prints_returned_access_token(monkeypatch, capsys):
    returned_token = "sensitive-access-token-value"
    monkeypatch.setenv("IBOOKS_ADMIN_PASSWORD", "test-login-password")
    monkeypatch.setattr(
        login_script.httpx,
        "post",
        lambda *args, **kwargs: type(
            "Response",
            (),
            {
                "status_code": 200,
                "json": lambda self: {"access_token": returned_token},
            },
        )(),
    )

    login_script.main()

    output = capsys.readouterr().out
    assert returned_token not in output
    assert "access token received but not displayed" in output


def test_management_scripts_do_not_embed_known_credentials():
    backend_root = Path(__file__).resolve().parents[1]
    targets = [
        backend_root / "create_admin.py",
        backend_root / "reset_admin_password.py",
        backend_root / "app/scripts/check_admin.py",
        backend_root / "app/scripts/recreate_admin.py",
        backend_root / "app/scripts/debug_jwt.py",
        backend_root / "app/scripts/test_login.py",
        backend_root / "scripts/seed_test_data.py",
    ]

    for target in targets:
        tree = ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
        string_literals = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ]
        assert all("admin123" not in value.lower() for value in string_literals)
        assert all(not value.startswith("eyJ") for value in string_literals)
