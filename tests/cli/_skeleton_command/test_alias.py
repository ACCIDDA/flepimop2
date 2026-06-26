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
"""Tests for the deprecated `flepimop2 skeleton` alias."""

from pathlib import Path

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


def test_skeleton_alias_still_scaffolds(tmp_path: Path) -> None:
    """`skeleton <path>` still produces the same project as `pattern`."""
    target = tmp_path / "project"

    result = CliRunner().invoke(cli, ["skeleton", str(target)], catch_exceptions=False)

    assert result.exit_code == ExitCode.OKAY
    assert _relative_files(target) == _relative_files(_TEMPLATE_DIR)


def test_skeleton_alias_warns_about_deprecation(tmp_path: Path) -> None:
    """`skeleton` emits a deprecation notice pointing to `pattern`."""
    target = tmp_path / "project"

    result = CliRunner().invoke(cli, ["skeleton", str(target)], catch_exceptions=False)

    assert result.exit_code == ExitCode.OKAY
    assert "deprecated" in result.output.lower()
    assert "pattern" in result.output.lower()
