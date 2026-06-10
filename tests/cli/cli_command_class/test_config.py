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
"""Tests for `CliCommand.config` metadata."""

from pathlib import Path

from flepimop2.cli import CliCommand
from flepimop2.cli._build_command import BuildCommand
from flepimop2.cli._format_command import FormatCommand
from flepimop2.cli._patch_command import PatchCommand
from flepimop2.cli._process_command import ProcessCommand
from flepimop2.cli._simulate_command import SimulateCommand
from flepimop2.cli._skeleton_command import SkeletonCommand
from flepimop2.typing import ExitCode, PatchConflictMode


class _ConfiglessCommand(CliCommand):
    """Command with no primary configuration path."""

    def run(self) -> ExitCode:  # type: ignore[override]
        """Execute the command.

        Returns:
            Exit code.
        """
        return ExitCode.OKAY


def test_base_config_defaults_to_none() -> None:
    """Commands should be configless unless they bind a singular config."""
    assert _ConfiglessCommand().config is None


def test_base_config_returns_bound_path(tmp_path: Path) -> None:
    """The default implementation should return bound Path config values."""
    config = tmp_path / "config.yaml"

    assert _ConfiglessCommand(config=config).config == config


def test_base_config_coerces_bound_string() -> None:
    """String config values should be exposed as Path instances."""
    assert _ConfiglessCommand(config="config.yaml").config == Path("config.yaml")


def test_singular_config_builtin_commands_return_config(tmp_path: Path) -> None:
    """Commands that bind `config` should expose it as their primary config path."""
    config = tmp_path / "config.yaml"

    assert BuildCommand(config=config).config == config
    assert FormatCommand(config=config).config == config
    assert ProcessCommand(config=config).config == config
    assert SimulateCommand(config=config).config == config


def test_patch_command_config_is_none(tmp_path: Path) -> None:
    """PatchCommand has multiple input configs and no singular primary config."""
    base = tmp_path / "base.yaml"
    patch = tmp_path / "patch.yaml"
    command = PatchCommand(
        configs=(base, patch),
        dry_run=False,
        output=None,
        patch_mode=PatchConflictMode.ERROR,
    )

    assert command.config is None


def test_skeleton_command_config_is_none(tmp_path: Path) -> None:
    """SkeletonCommand acts on a filesystem path, not a config file."""
    assert SkeletonCommand(path=tmp_path, dry_run=False).config is None
