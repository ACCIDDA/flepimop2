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
"""Tests for `CopyPattern.scaffold`."""

import tarfile
import zipfile
from pathlib import Path

import pytest

from flepimop2.pattern.copy import _TEMPLATE_DIR, CopyPattern


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

    CopyPattern().scaffold(destination)

    assert _relative_files(destination) == _relative_files(_TEMPLATE_DIR)
    for relative_path in _relative_files(_TEMPLATE_DIR):
        assert (destination / relative_path).read_text() == (
            _TEMPLATE_DIR / relative_path
        ).read_text()


def test_scaffold_dry_run_writes_nothing(tmp_path: Path) -> None:
    """A dry-run `scaffold` performs no filesystem writes."""
    destination = tmp_path / "project"

    CopyPattern().scaffold(destination, dry_run=True)

    assert not destination.exists()


def test_plan_describes_the_template_without_writing() -> None:
    """`plan` renders the template tree and touches no filesystem destination."""
    tree = CopyPattern().plan()

    assert tree.strip()
    for relative_path in _relative_files(_TEMPLATE_DIR):
        assert relative_path.name in tree


def test_source_overrides_the_bundled_template(tmp_path: Path) -> None:
    """A `source` copies from that directory instead of the bundled template."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "custom.txt").write_text("hello")
    destination = tmp_path / "out"

    CopyPattern(source=source).scaffold(destination)

    assert (destination / "custom.txt").read_text() == "hello"
    assert "custom.txt" in CopyPattern(source=source).plan()


@pytest.mark.parametrize("archive_type", ["zip", "tar"])
def test_archive_source_is_unpacked(tmp_path: Path, archive_type: str) -> None:
    """A local zip or tar source is unpacked into the destination."""
    source = tmp_path / "source"
    (source / "nested").mkdir(parents=True)
    (source / "top.yaml").write_text("x: 1")
    (source / "nested" / "inner.txt").write_text("hello")
    archive_path = tmp_path / f"source.{archive_type}"
    if archive_type == "zip":
        with zipfile.ZipFile(archive_path, "w") as archive:
            for path in source.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(source))
    else:
        with tarfile.open(archive_path, "w") as archive:
            for path in source.rglob("*"):
                archive.add(path, path.relative_to(source), recursive=False)

    destination = tmp_path / "out"
    pattern = CopyPattern(source=archive_path)
    pattern.scaffold(destination)

    assert (destination / "top.yaml").read_text() == "x: 1"
    assert (destination / "nested" / "inner.txt").read_text() == "hello"
    assert "inner.txt" in pattern.plan()


def test_archive_source_rejects_parent_traversal(tmp_path: Path) -> None:
    """An archive member cannot write outside the destination."""
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "unsafe")

    with pytest.raises(ValueError, match="escapes the target"):
        CopyPattern(source=archive_path).scaffold(tmp_path / "out")

    assert not (tmp_path / "outside.txt").exists()


def test_a_source_that_is_not_a_directory_is_rejected(tmp_path: Path) -> None:
    """A `source` pointing at a missing path raises rather than scaffolding."""
    pattern = CopyPattern(source=tmp_path / "does_not_exist")

    with pytest.raises(ValueError, match="does not exist"):
        pattern.scaffold(tmp_path / "out")
