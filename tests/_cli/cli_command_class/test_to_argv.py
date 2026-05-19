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
"""Tests for `CliCommand.to_argv`."""

from pathlib import Path

from flepimop2._cli._cli_command import CliCommand
from flepimop2.typing import ExitCode


class _FlagCommand(CliCommand):
    """Command with a flag option (dry_run) and auto-appended verbosity."""

    def run(self, *, dry_run: bool, verbosity: int) -> ExitCode:  # type: ignore[override]
        """Execute the command.

        Returns:
            Exit code.
        """
        del dry_run, verbosity
        return ExitCode.OKAY


class _ConfigCommand(CliCommand):
    """Command whose sole option is the config positional argument."""

    auto_append_verbosity = False

    def run(self, *, config: Path) -> ExitCode:  # type: ignore[override]
        """Execute the command.

        Returns:
            Exit code.
        """
        del config
        return ExitCode.OKAY


class _TargetCommand(CliCommand):
    """Command with a --target string option."""

    auto_append_verbosity = False

    def run(self, *, target: str | None) -> ExitCode:  # type: ignore[override]
        """Execute the command.

        Returns:
            Exit code.
        """
        del target
        return ExitCode.OKAY


def test_config_absolute_path(tmp_path: Path) -> None:
    """Config argument should be rendered as an absolute path string."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("x: 1\n")
    cmd = _ConfigCommand(config=cfg)
    assert cmd.to_argv() == [str(cfg.absolute())]


def test_config_none_omitted() -> None:
    """If config is None, it should be omitted from argv."""
    cmd = _ConfigCommand(config=None)
    assert cmd.to_argv() == []


def test_flag_true() -> None:
    """A truthy is_flag option should appear as its flag token."""
    cmd = _FlagCommand(dry_run=True, verbosity=0)
    assert "--dry-run" in cmd.to_argv()


def test_flag_false_omitted() -> None:
    """A falsy is_flag option should be omitted entirely."""
    cmd = _FlagCommand(dry_run=False, verbosity=0)
    assert "--dry-run" not in cmd.to_argv()


def test_verbosity_zero_omitted() -> None:
    """Verbosity of 0 should produce no token."""
    cmd = _FlagCommand(dry_run=False, verbosity=0)
    assert not any(t.startswith("-v") for t in cmd.to_argv())


def test_verbosity_one() -> None:
    """-v should appear once for verbosity=1."""
    cmd = _FlagCommand(dry_run=False, verbosity=1)
    assert "-v" in cmd.to_argv()


def test_verbosity_three() -> None:
    """-vvv should appear for verbosity=3."""
    cmd = _FlagCommand(dry_run=False, verbosity=3)
    assert "-vvv" in cmd.to_argv()


def test_target_present() -> None:
    """A set --target value should produce ['--target', value]."""
    cmd = _TargetCommand(target="sim1")
    argv = cmd.to_argv()
    assert "--target" in argv
    assert argv[argv.index("--target") + 1] == "sim1"


def test_target_none_omitted() -> None:
    """A None --target should be omitted from argv."""
    cmd = _TargetCommand(target=None)
    assert "--target" not in cmd.to_argv()


def test_order_matches_options() -> None:
    """Tokens should appear in the same order as cls.options()."""
    cmd = _FlagCommand(dry_run=True, verbosity=2)
    argv = cmd.to_argv()
    assert argv.index("--dry-run") < argv.index("-vv")
