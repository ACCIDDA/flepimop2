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
"""Tests for shared config argument resolution in `flepimop2._cli._options`."""

from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from flepimop2._cli._options import (
    _resolve_config_argument,
    get_option,
)


def test_resolve_config_argument_returns_explicit_value(tmp_path: Path) -> None:
    """An explicit config path should bypass default search resolution."""
    config_path = tmp_path / "custom.yaml"
    config_path.write_text("name: explicit\n")

    assert _resolve_config_argument(config_path) == config_path


def test_resolve_config_argument_uses_first_match_in_search_order(
    tmp_path: Path,
) -> None:
    """The first matching default config path should win."""
    first_match = tmp_path / "configuration.yml"
    first_match.write_text("name: first\n")
    later_match = tmp_path / "configs" / "config.yaml"
    later_match.parent.mkdir()
    later_match.write_text("name: later\n")

    assert _resolve_config_argument(None, cwd=tmp_path) == first_match


def test_resolve_config_argument_prefers_yaml_before_yml(tmp_path: Path) -> None:
    """`.yaml` should win over `.yml` when both names exist for a pattern."""
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text("name: yaml\n")
    yml_path = tmp_path / "config.yml"
    yml_path.write_text("name: yml\n")

    assert _resolve_config_argument(None, cwd=tmp_path) == yaml_path


def test_resolve_config_argument_raises_when_no_default_found(tmp_path: Path) -> None:
    """Missing default configs should produce a useful error."""
    msg = "No configuration file was provided and none was found"

    with pytest.raises(FileNotFoundError, match=msg) as exc_info:
        _resolve_config_argument(None, cwd=tmp_path)

    assert str(tmp_path / "config.yaml") in str(exc_info.value)


def test_common_config_argument_uses_default_search(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The shared Click argument should resolve a default config when omitted."""
    config_path = tmp_path / "configs" / "configuration.yaml"
    config_path.parent.mkdir()
    config_path.write_text("name: resolved\n")
    monkeypatch.chdir(tmp_path)

    @click.command()
    @get_option("config")
    def command(config: Path) -> None:
        click.echo(str(config))

    runner = CliRunner()
    result = runner.invoke(command, [], catch_exceptions=False)

    assert result.exit_code == 0
    assert result.output.strip() == str(config_path)


def test_common_config_argument_reports_missing_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The shared Click argument should fail clearly when no config is found."""
    monkeypatch.chdir(tmp_path)

    @click.command()
    @get_option("config")
    def command(config: Path) -> None:
        click.echo(str(config))

    runner = CliRunner()
    result = runner.invoke(command, [], catch_exceptions=False)

    assert result.exit_code != 0
    assert "Invalid value for '[CONFIG]'" in result.output
    assert "No configuration file was provided and none was found" in result.output
