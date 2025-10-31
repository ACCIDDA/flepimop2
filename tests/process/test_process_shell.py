"""Tests for `ProcessABC` default `ShellProcess`."""

from typing import Any

import pytest

import flepimop2.process as process_module


@pytest.mark.parametrize("config", [{"command": "echo", "args": ["Hello, World!"]}])
def test_shell_system(config: dict[str, Any]) -> None:
    """Test `ShellProcess` makes a command and executes it."""
    process = process_module.build(config)
    process.execute()
