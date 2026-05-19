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
"""Tests for `flepimop2._utils._click._render_param`."""

from pathlib import Path

import click
import pytest

from flepimop2._utils._click import _render_param


def test_argument_string_value() -> None:
    """A string positional argument should render as a bare token."""
    param = click.Argument(["config"])
    assert _render_param(param, "config.yaml") == ["config.yaml"]


def test_argument_path_value(tmp_path: Path) -> None:
    """A Path positional argument should render as its absolute path."""
    p = tmp_path / "config.yaml"
    param = click.Argument(["config"])
    assert _render_param(param, p) == [str(p.absolute())]


def test_argument_none_omitted() -> None:
    """A None positional argument should produce no tokens."""
    param = click.Argument(["config"])
    assert _render_param(param, None) == []


def test_flag_true_emits_flag_token() -> None:
    """A truthy flag option should emit the flag token."""
    param = click.Option(["--dry-run"], is_flag=True, default=False)
    value: bool = True
    assert _render_param(param, value) == ["--dry-run"]


def test_flag_false_omitted() -> None:
    """A falsy flag option should produce no tokens."""
    param = click.Option(["--dry-run"], is_flag=True, default=False)
    value: bool = False
    assert _render_param(param, value) == []


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (0, []),
        (1, ["-v"]),
        (3, ["-vvv"]),
    ],
)
def test_count_option(count: int, expected: list[str]) -> None:
    """Count options should render as repeated short flags."""
    param = click.Option(["-v", "--verbosity"], count=True, default=0)
    assert _render_param(param, count) == expected


def test_regular_option_string() -> None:
    """A regular option with a string value should produce ['--name', value]."""
    param = click.Option(["-t", "--target"], default=None)
    assert _render_param(param, "sim1") == ["--target", "sim1"]


def test_regular_option_none_omitted() -> None:
    """A None regular option should produce no tokens."""
    param = click.Option(["-t", "--target"], default=None)
    assert _render_param(param, None) == []


def test_regular_option_path_absolute(tmp_path: Path) -> None:
    """A Path regular option should render as its absolute path."""
    p = tmp_path / "output"
    param = click.Option(["--output"], default=None)
    result = _render_param(param, p)
    assert result == ["--output", str(p.absolute())]
