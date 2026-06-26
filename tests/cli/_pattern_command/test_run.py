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
"""Tests for `PatternCommand.run` via the `flepimop2 pattern` CLI."""

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from flepimop2.cli._cli import cli
from flepimop2.pattern.default import _TEMPLATE_DIR
from flepimop2.typing import ExitCode


def _relative_files(root: Path) -> set[Path]:
    """
    Collect every file beneath `root`, as paths relative to `root`.

    Args:
        root: The directory tree to walk.

    Returns:
        The set of contained file paths, relative to `root`.
    """
    return {path.relative_to(root) for path in root.rglob("*") if path.is_file()}


def test_run_scaffolds_full_template_tree(tmp_path: Path) -> None:
    """`pattern <path>` reproduces the bundled template tree, contents and all."""
    target = tmp_path / "nested" / "project"

    result = CliRunner().invoke(cli, ["pattern", str(target)], catch_exceptions=False)

    assert result.exit_code == ExitCode.OKAY
    assert _relative_files(target) == _relative_files(_TEMPLATE_DIR)
    for relative_path in _relative_files(_TEMPLATE_DIR):
        assert (target / relative_path).read_text() == (
            _TEMPLATE_DIR / relative_path
        ).read_text()


def test_run_defaults_to_current_directory() -> None:
    """`pattern` with no path argument scaffolds into the working directory."""
    runner = CliRunner()
    with runner.isolated_filesystem() as filesystem:
        result = runner.invoke(cli, ["pattern"], catch_exceptions=False)

        assert result.exit_code == ExitCode.OKAY
        assert _relative_files(Path(filesystem)) == _relative_files(_TEMPLATE_DIR)


def test_run_dry_run_reports_target_without_writing(tmp_path: Path) -> None:
    """`pattern --dry-run` reports the target but creates nothing on disk."""
    target = tmp_path / "project"

    result = CliRunner().invoke(
        cli,
        ["pattern", "--dry-run", "-vv", str(target)],
        catch_exceptions=False,
    )

    assert result.exit_code == ExitCode.OKAY
    assert not target.exists()
    assert "Would create project at" in result.output


def test_run_returns_general_when_target_not_writable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-writable nearest-existing ancestor yields `ExitCode.GENERAL`."""
    target = tmp_path / "project"

    def _deny_writes(path: object, mode: int, *args: object, **kwargs: object) -> bool:
        """
        Report every path as readable and executable but never writable.

        Args:
            path: The path being probed (unused).
            mode: The access mode being checked.
            *args: Extra positional arguments accepted by `os.access`.
            **kwargs: Extra keyword arguments accepted by `os.access`.

        Returns:
            `False` for write probes, `True` for any other access check.
        """
        del path, args, kwargs
        return mode != os.W_OK

    monkeypatch.setattr(os, "access", _deny_writes)

    result = CliRunner().invoke(cli, ["pattern", str(target)], catch_exceptions=False)

    assert result.exit_code == ExitCode.GENERAL
    assert not target.exists()
    assert "Cannot write to path" in result.output
