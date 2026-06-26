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
"""Tests for `DefaultPattern.scaffold`."""

from pathlib import Path

from flepimop2.pattern.default import _TEMPLATE_DIR, DefaultPattern


def _relative_files(root: Path) -> set[Path]:
    """
    Collect every file beneath `root`, as paths relative to `root`.

    Args:
        root: The directory tree to walk.

    Returns:
        The set of contained file paths, relative to `root`.
    """
    return {path.relative_to(root) for path in root.rglob("*") if path.is_file()}


def test_scaffold_reproduces_template_tree(tmp_path: Path) -> None:
    """`scaffold` reproduces the bundled template tree, contents and all."""
    destination = tmp_path / "nested" / "project"

    DefaultPattern().scaffold(destination)

    assert _relative_files(destination) == _relative_files(_TEMPLATE_DIR)
    for relative_path in _relative_files(_TEMPLATE_DIR):
        assert (destination / relative_path).read_text() == (
            _TEMPLATE_DIR / relative_path
        ).read_text()


def test_scaffold_dry_run_writes_nothing(tmp_path: Path) -> None:
    """A dry-run `scaffold` performs no filesystem writes."""
    destination = tmp_path / "project"

    DefaultPattern().scaffold(destination, dry_run=True)

    assert not destination.exists()
