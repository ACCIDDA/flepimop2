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
"""Tests for the `flepimop2 format` CLI command."""

from pathlib import Path

from click.testing import CliRunner

from flepimop2.cli._cli import cli
from flepimop2.typing import ExitCode


def test_format_command_rewrites_configuration_in_place(tmp_path: Path) -> None:
    """Formatting should normalize YAML in place by default."""
    config = tmp_path / "config.yaml"
    config.write_text(
        """
name: ""
engines:
  default:
    module: demo.engine
    options: {}
systems: {}
""".lstrip(),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["format", str(config)],
        catch_exceptions=False,
    )

    assert result.exit_code == ExitCode.OKAY
    assert not result.output
    assert config.read_text(encoding="utf-8") == "engines:\n- module: demo.engine\n"


def test_format_command_check_fails_when_configuration_would_change(
    tmp_path: Path,
) -> None:
    """Check mode should fail without modifying an unformatted file."""
    config = tmp_path / "config.yaml"
    original = """
name: ""
engines:
  default:
    module: demo.engine
    options: {}
""".lstrip()
    config.write_text(original, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["format", "--check", str(config)],
        catch_exceptions=False,
    )

    assert result.exit_code == ExitCode.GENERAL
    assert "is not formatted" in result.output
    assert config.read_text(encoding="utf-8") == original


def test_format_command_dry_run_prints_formatted_yaml(tmp_path: Path) -> None:
    """Dry-run mode should print the normalized YAML without rewriting the file."""
    config = tmp_path / "config.yaml"
    original = """
engines:
  default:
    module: demo.engine
    options: {}
""".lstrip()
    config.write_text(original, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["format", "--dry-run", str(config)],
        catch_exceptions=False,
    )

    assert result.exit_code == ExitCode.OKAY
    assert result.output == "engines:\n- module: demo.engine\n"
    assert config.read_text(encoding="utf-8") == original


def test_format_command_preserves_explicit_document_start(
    tmp_path: Path,
) -> None:
    """Formatting should keep `---` when the original file includes it."""
    config = tmp_path / "config.yaml"
    original = """
---
engines:
  default:
    module: demo.engine
    options: {}
""".lstrip()
    config.write_text(original, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["format", str(config)],
        catch_exceptions=False,
    )

    assert result.exit_code == ExitCode.OKAY
    assert not result.output
    assert config.read_text(encoding="utf-8") == (
        "---\nengines:\n- module: demo.engine\n"
    )


def test_format_command_dry_run_preserves_explicit_document_start(
    tmp_path: Path,
) -> None:
    """Dry-run output should keep `---` when the original file includes it."""
    config = tmp_path / "config.yaml"
    original = """
---
engines:
  default:
    module: demo.engine
    options: {}
""".lstrip()
    config.write_text(original, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["format", "--dry-run", str(config)],
        catch_exceptions=False,
    )

    assert result.exit_code == ExitCode.OKAY
    assert result.output == "---\nengines:\n- module: demo.engine\n"
    assert config.read_text(encoding="utf-8") == original
