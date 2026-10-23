# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Tests for `ProcessABC` default `ShellProcess`."""

import shlex
import sys
from pathlib import Path
from subprocess import CompletedProcess  # noqa: S404
from typing import Any

import pytest

from flepimop2.exceptions import Flepimop2ValidationError
from flepimop2.process.abc import build as build_process


@pytest.mark.parametrize(
    "config",
    [{"module": "shell", "command": "echo", "args": ["Hello, World!"]}],
)
def test_shell_system(config: dict[str, Any]) -> None:
    """Test `ShellProcess` makes a command and executes it."""
    process = build_process(config)
    process.execute()


def test_shell_process_shorthand_not_supported() -> None:
    """Shell process should reject shorthand until it opts in."""
    with pytest.raises(
        ValueError,
        match=(
            r"Module 'flepimop2\.process\.shell' does not support shorthand "
            r"configuration\."
        ),
    ):
        build_process("shell(echo, hello)")


def test_shell_process_preserves_argument_boundaries(tmp_path: Path) -> None:
    """Arguments containing spaces reach the child as one argv element."""
    output = tmp_path / "argv.txt"
    process = build_process({
        "module": "shell",
        "command": sys.executable,
        "args": [
            "-c",
            (
                "from pathlib import Path; import sys; "
                "Path(sys.argv[1]).write_text(sys.argv[2])"
            ),
            str(output),
            "not benchmark",
        ],
    })

    process.execute()

    assert output.read_text() == "not benchmark"


def test_shell_process_dry_run_prints_without_executing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Dry runs render shell-safe argv and do not start the command."""
    output = tmp_path / "should-not-exist.txt"
    args = [
        "-c",
        "from pathlib import Path; import sys; Path(sys.argv[1]).touch()",
        str(output),
    ]
    process = build_process({
        "module": "shell",
        "command": sys.executable,
        "args": args,
    })

    process.execute(dry_run=True)

    assert not output.exists()
    assert capsys.readouterr().out.strip() == shlex.join([sys.executable, *args])


@pytest.mark.parametrize(
    "command", ["Rscript postprocessing/plot.R", "python\tplot.py"]
)
@pytest.mark.parametrize("dry_run", [False, True])
def test_shell_process_rejects_multiword_command(
    command: str, *, dry_run: bool
) -> None:
    """Validation and execution explain where script arguments belong."""
    process = build_process({"module": "shell", "command": command})
    issues = process.validate_module()
    assert len(issues) == 1
    assert issues[0].kind == "invalid_command"
    assert "single executable" in issues[0].msg
    assert "args" in issues[0].msg
    with pytest.raises(Flepimop2ValidationError, match="single executable"):
        process.execute(dry_run=dry_run)


@pytest.mark.parametrize("use_path", [False, True])
def test_shell_process_allows_executable_names_with_spaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, use_path: bool
) -> None:
    """Existing executable paths and PATH entries remain one argv element."""
    executable = tmp_path / "helper tool.exe"
    executable.write_bytes(b"")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    command = str(executable) if use_path else executable.name
    calls: list[list[str]] = []

    def run_command(cmd: list[str], *, check: bool) -> CompletedProcess[bytes]:
        assert check is False
        calls.append(cmd)
        return CompletedProcess(cmd, 0)

    monkeypatch.setattr("flepimop2.process.shell.run", run_command)
    process = build_process({
        "module": "shell",
        "command": command,
        "args": ["script with spaces.py"],
    })
    assert process.validate_module() == []
    process.execute()
    assert calls == [[command, "script with spaces.py"]]


def test_shell_process_validates_at_execution_time(tmp_path: Path) -> None:
    """An upstream process may create the executable after config loading."""
    executable = tmp_path / "generated tool.exe"
    process = build_process({"module": "shell", "command": str(executable)})
    assert process.validate_module()
    executable.write_bytes(b"")
    assert process.validate_module() == []
