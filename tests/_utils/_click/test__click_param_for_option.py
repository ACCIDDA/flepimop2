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
"""Tests for `flepimop2._utils._click._click_param_for_option`."""

import click

from flepimop2._utils._click import _click_param_for_option


def test_returns_option_for_option_decorator() -> None:
    """A click.option decorator should yield a ClickOption instance."""
    decorator = click.option("--dry-run", is_flag=True, default=False)
    param = _click_param_for_option(decorator)
    assert isinstance(param, click.Option)
    assert param.name == "dry_run"


def test_returns_argument_for_argument_decorator() -> None:
    """A click.argument decorator should yield a ClickArgument instance."""
    decorator = click.argument("config")
    param = _click_param_for_option(decorator)
    assert isinstance(param, click.Argument)
    assert param.name == "config"


def test_returns_none_for_identity_decorator() -> None:
    """A no-op decorator that attaches no params should return None."""
    param = _click_param_for_option(lambda f: f)
    assert param is None
