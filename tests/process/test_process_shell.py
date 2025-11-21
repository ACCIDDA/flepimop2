"""Tests for `ProcessABC` default `ShellProcess`."""

from typing import Any

import pytest

from flepimop2.process.abc import build as build_process


@pytest.mark.parametrize("config", [{"command": "echo", "args": ["Hello, World!"]}])
def test_shell_system(config: dict[str, Any]) -> None:
    """Test `ShellProcess` makes a command and executes it."""
    process = build_process(config)
    process.execute()
