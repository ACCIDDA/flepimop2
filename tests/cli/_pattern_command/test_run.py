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
import zipfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from flepimop2.cli._cli import cli
from flepimop2.pattern.copy import _TEMPLATE_DIR
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
    assert "Would create a project at" in result.output
    assert "using the 'copy' pattern" in result.output


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


def test_run_module_option_selects_the_copy_pattern(tmp_path: Path) -> None:
    """`--module copy` scaffolds the same tree as the default."""
    target = tmp_path / "project"

    result = CliRunner().invoke(
        cli, ["pattern", "--module", "copy", str(target)], catch_exceptions=False
    )

    assert result.exit_code == ExitCode.OKAY
    assert _relative_files(target) == _relative_files(_TEMPLATE_DIR)


def test_run_unknown_module_errors_without_writing(tmp_path: Path) -> None:
    """An unregistered `--module` reports a clean error and writes nothing."""
    target = tmp_path / "project"

    result = CliRunner().invoke(
        cli,
        ["pattern", "--module", "no_such_pattern", str(target)],
        catch_exceptions=False,
    )

    assert result.exit_code == ExitCode.GENERAL
    assert not target.exists()
    assert "Unknown pattern module" in result.output


def test_run_source_option_copies_the_given_tree(tmp_path: Path) -> None:
    """`--source` copies from the given directory instead of the bundled template."""
    source = tmp_path / "source"
    (source / "sub").mkdir(parents=True)
    (source / "top.yaml").write_text("x: 1")
    (source / "sub" / "inner.txt").write_text("hi")
    target = tmp_path / "project"

    result = CliRunner().invoke(
        cli, ["pattern", "--source", str(source), str(target)], catch_exceptions=False
    )

    assert result.exit_code == ExitCode.OKAY
    assert _relative_files(target) == _relative_files(source)
    assert (target / "sub" / "inner.txt").read_text() == "hi"


def test_run_source_option_unpacks_a_local_archive(tmp_path: Path) -> None:
    """`--source` accepts a local archive as well as a directory."""
    archive_path = tmp_path / "project.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("configs/config.yaml", "name: archived")
    target = tmp_path / "project"

    result = CliRunner().invoke(
        cli, ["pattern", "--source", str(archive_path), str(target)]
    )

    assert result.exit_code == ExitCode.OKAY
    assert (target / "configs" / "config.yaml").read_text() == "name: archived"


def test_run_rejects_an_unsupported_source_file(tmp_path: Path) -> None:
    """An unsupported source file reports a clean command error."""
    source = tmp_path / "project.txt"
    source.write_text("not an archive")
    target = tmp_path / "project"

    result = CliRunner().invoke(cli, ["pattern", "--source", str(source), str(target)])

    assert result.exit_code == ExitCode.GENERAL
    assert "not a supported zip or tar archive" in result.output
    assert not target.exists()


def test_run_module_short_flag_selects_the_pattern(tmp_path: Path) -> None:
    """`-m` is a shorthand for `--module`."""
    target = tmp_path / "project"

    result = CliRunner().invoke(
        cli, ["pattern", "-m", "copy", str(target)], catch_exceptions=False
    )

    assert result.exit_code == ExitCode.OKAY
    assert _relative_files(target) == _relative_files(_TEMPLATE_DIR)


def test_run_refuses_to_overwrite_existing_files(tmp_path: Path) -> None:
    """Scaffolding refuses when it would overwrite files already in the target."""
    target = tmp_path / "project"
    target.mkdir()
    # README.md is part of the bundled template, so this is a genuine clobber.
    (target / "README.md").write_text("do not clobber")

    result = CliRunner().invoke(cli, ["pattern", str(target)], catch_exceptions=False)

    assert result.exit_code == ExitCode.GENERAL
    assert "overwrite" in result.output
    assert (target / "README.md").read_text() == "do not clobber"


def test_run_scaffolds_alongside_unrelated_files(tmp_path: Path) -> None:
    """A target holding only non-conflicting content (e.g. a venv) still scaffolds."""
    target = tmp_path / "project"
    (target / ".venv").mkdir(parents=True)
    (target / ".venv" / "marker").write_text("keep")

    result = CliRunner().invoke(cli, ["pattern", str(target)], catch_exceptions=False)

    assert result.exit_code == ExitCode.OKAY
    assert (target / "README.md").exists()
    assert (target / ".venv" / "marker").read_text() == "keep"
