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
"""Tests for `CliCommand.target` metadata."""

from pathlib import Path

from flepimop2.cli import CliCommand
from flepimop2.cli._format_command import FormatCommand
from flepimop2.cli._patch_command import PatchCommand
from flepimop2.cli._process_command import ProcessCommand
from flepimop2.cli._simulate_command import SimulateCommand
from flepimop2.cli._skeleton_command import SkeletonCommand
from flepimop2.typing import ExitCode


class _TargetlessCommand(CliCommand):
    """Command with no logical configuration target."""

    def run(self) -> ExitCode:  # type: ignore[override]
        """Execute the command.

        Returns:
            Exit code.
        """
        return ExitCode.OKAY


def test_base_target_defaults_to_none() -> None:
    """Commands should be targetless unless they opt into target metadata."""
    assert _TargetlessCommand().target is None


def test_targetless_builtin_commands_return_none() -> None:
    """Format, patch, and skeleton commands do not act on named config targets."""
    assert FormatCommand().target is None
    assert PatchCommand().target is None
    assert SkeletonCommand().target is None


def test_process_target_returns_explicit_target(tmp_path: Path) -> None:
    """ProcessCommand.target should return the named process target."""
    config = tmp_path / "config.yaml"
    config.write_text(
        """
process:
  preprocess:
    module: demo.process
  postprocess:
    module: demo.process
""".lstrip(),
        encoding="utf-8",
    )

    cmd = ProcessCommand(config=config, target="postprocess")

    assert cmd.target == "postprocess"


def test_process_target_returns_implicit_default_target(tmp_path: Path) -> None:
    """ProcessCommand.target should resolve the first process entry by default."""
    config = tmp_path / "config.yaml"
    config.write_text(
        """
process:
  preprocess:
    module: demo.process
  postprocess:
    module: demo.process
""".lstrip(),
        encoding="utf-8",
    )

    cmd = ProcessCommand(config=config, target=None)

    assert cmd.target == "preprocess"


def test_simulate_target_returns_explicit_target(tmp_path: Path) -> None:
    """SimulateCommand.target should return the named simulate target."""
    config = tmp_path / "config.yaml"
    config.write_text(
        """
engines:
  default:
    module: demo.engine
systems:
  default:
    module: demo.system
backends:
  default:
    module: demo.backend
simulate:
  baseline:
    times: [0.0, 1.0]
  intervention:
    times: [0.0, 2.0]
""".lstrip(),
        encoding="utf-8",
    )

    cmd = SimulateCommand(config=config, target="intervention")

    assert cmd.target == "intervention"


def test_simulate_target_returns_implicit_default_target(tmp_path: Path) -> None:
    """SimulateCommand.target should resolve the first simulate entry by default."""
    config = tmp_path / "config.yaml"
    config.write_text(
        """
engines:
  default:
    module: demo.engine
systems:
  default:
    module: demo.system
backends:
  default:
    module: demo.backend
simulate:
  baseline:
    times: [0.0, 1.0]
  intervention:
    times: [0.0, 2.0]
""".lstrip(),
        encoding="utf-8",
    )

    cmd = SimulateCommand(config=config, target=None)

    assert cmd.target == "baseline"
