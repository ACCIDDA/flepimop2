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
"""Tests for the `flepimop2 patch` CLI command."""

from pathlib import Path

from click.testing import CliRunner
from yaml import safe_load

from flepimop2.cli._cli import cli
from flepimop2.typing import ExitCode


def test_patch_command_patches_configs_in_order_to_stdout(tmp_path: Path) -> None:
    """Patch mode `merge` should apply configurations from left to right."""
    base = tmp_path / "base.yaml"
    base.write_text(
        """
name: base
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
  main:
    times: [0.0, 1.0]
    params:
      alpha: 1.0
""".lstrip(),
        encoding="utf-8",
    )
    patch_one = tmp_path / "patch-one.yaml"
    patch_one.write_text(
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
  main:
    times: [0.0, 1.0]
    params:
      beta: 2.0
""".lstrip(),
        encoding="utf-8",
    )
    patch_two = tmp_path / "patch-two.yaml"
    patch_two.write_text(
        """
name: final
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
  main:
    times: [0.0, 2.0]
""".lstrip(),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "patch",
            "--patch-mode",
            "merge",
            str(base),
            str(patch_one),
            str(patch_two),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == ExitCode.OKAY
    assert safe_load(result.output) == {
        "name": "final",
        "engines": [{"module": "demo.engine"}],
        "systems": [{"module": "demo.system"}],
        "backends": [{"module": "demo.backend"}],
        "simulate": {
            "main": {
                "engine": "default",
                "system": "default",
                "backend": "default",
                "times": [0.0, 2.0],
                "params": {
                    "alpha": 1.0,
                    "beta": 2.0,
                },
            }
        },
    }


def test_patch_command_defaults_to_error_mode(tmp_path: Path) -> None:
    """Default patch mode should fail on duplicate top-level entry names."""
    base = tmp_path / "base.yaml"
    base.write_text(
        """
parameters:
  rate: fixed(1.0)
""".lstrip(),
        encoding="utf-8",
    )
    patch = tmp_path / "patch.yaml"
    patch.write_text(
        """
parameters:
  rate: fixed(2.0)
""".lstrip(),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["patch", str(base), str(patch)],
        catch_exceptions=False,
    )

    assert result.exit_code == ExitCode.CONFIGURATION
    assert "Cannot patch configuration under conflict='error'" in result.output


def test_patch_command_writes_output_file(tmp_path: Path) -> None:
    """`--output` should write the patched YAML instead of printing it."""
    base = tmp_path / "base.yaml"
    base.write_text(
        """
parameters:
  rate: fixed(1.0)
""".lstrip(),
        encoding="utf-8",
    )
    patch = tmp_path / "patch.yaml"
    patch.write_text(
        """
parameters:
  rate: fixed(2.0)
""".lstrip(),
        encoding="utf-8",
    )
    output = tmp_path / "patched.yaml"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "patch",
            "--patch-mode",
            "replace",
            "--output",
            str(output),
            str(base),
            str(patch),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == ExitCode.OKAY
    assert not result.output
    assert safe_load(output.read_text(encoding="utf-8")) == {
        "parameters": {
            "rate": 2.0,
        },
    }


def test_patch_command_dry_run_prints_to_stdout_even_with_output(
    tmp_path: Path,
) -> None:
    """`--dry-run` should print YAML and skip writing the output file."""
    base = tmp_path / "base.yaml"
    base.write_text(
        """
parameters:
  rate: fixed(1.0)
""".lstrip(),
        encoding="utf-8",
    )
    patch = tmp_path / "patch.yaml"
    patch.write_text(
        """
parameters:
  rate: fixed(2.0)
""".lstrip(),
        encoding="utf-8",
    )
    output = tmp_path / "patched.yaml"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "patch",
            "--dry-run",
            "--patch-mode",
            "replace",
            "--output",
            str(output),
            str(base),
            str(patch),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == ExitCode.OKAY
    assert safe_load(result.output) == {
        "parameters": {
            "rate": 2.0,
        },
    }
    assert not output.exists()


def test_patch_command_preserves_explicit_document_start_from_any_config(
    tmp_path: Path,
) -> None:
    """Patched output should keep `---` if any input config includes it."""
    base = tmp_path / "base.yaml"
    base.write_text(
        """
parameters:
  alpha: fixed(1.0)
""".lstrip(),
        encoding="utf-8",
    )
    patch = tmp_path / "patch.yaml"
    patch.write_text(
        """
---
parameters:
  beta: fixed(2.0)
""".lstrip(),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "patch",
            "--patch-mode",
            "merge",
            str(base),
            str(patch),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == ExitCode.OKAY
    assert result.output.startswith("---\n")
    assert safe_load(result.output) == {
        "parameters": {
            "alpha": 1.0,
            "beta": 2.0,
        },
    }
