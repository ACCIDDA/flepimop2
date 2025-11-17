"""Tests for `ProcessABC` default `ShellProcess`."""

from typing import Any

import pytest

from flepimop2.process.shell import build


@pytest.mark.parametrize("config", [{"command": "echo", "args": ["Hello, World!"]}])
def test_shell_system(config: dict[str, Any]) -> None:
    """Test `ShellProcess` makes a command and executes it."""
    process = build(config)
    process.execute()
