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
"""Tests for the `COMMON_OPTIONS` constant in `flepimop2._cli._options`."""

from collections import Counter
from collections.abc import Callable

import click

from flepimop2._cli._options import COMMON_OPTIONS


def _click_param_from_decorator(
    decorator: Callable[[Callable[[], None]], Callable[[], None]],
) -> click.Parameter:
    """
    Materialize a Click parameter from a common option decorator.

    Returns:
        The single Click parameter attached by the decorator.
    """

    def callback() -> None:
        return None

    decorated = decorator(callback)
    click_params = getattr(decorated, "__click_params__", None)
    assert click_params is not None
    assert len(click_params) == 1
    assert isinstance(click_params[0], click.Parameter)
    return click_params[0]


def test_common_options_keys_are_sorted() -> None:
    """Test that COMMON_OPTIONS dictionary keys are sorted alphabetically."""
    keys = list(COMMON_OPTIONS.keys())
    sorted_keys = sorted(keys)
    assert keys == sorted_keys, (
        f"COMMON_OPTIONS keys are not sorted. Expected: {sorted_keys}, Got: {keys}"
    )


def test_no_duplicate_option_names() -> None:
    """Test that no two options share the same flag (e.g., -v, --verbosity)."""
    # Collect all option names from the decorators
    # Click decorators store the option names in their closure (3rd element)
    all_opts: list[str] = []
    for decorator, _help_text in COMMON_OPTIONS.values():
        if hasattr(decorator, "__closure__") and decorator.__closure__:
            # The option names are typically in the 3rd closure cell (index 2)
            # This contains a tuple like ('-v', '--verbosity') or ('config',)
            for cell in decorator.__closure__:
                cell_contents = cell.cell_contents
                if isinstance(cell_contents, tuple) and all(
                    isinstance(item, str) for item in cell_contents
                ):
                    all_opts.extend(cell_contents)
                    break

    # Check for duplicates
    opts_counter = Counter(all_opts)
    duplicates = {opt: count for opt, count in opts_counter.items() if count > 1}

    assert not duplicates, (
        f"Found duplicate option names in COMMON_OPTIONS: "
        f"{', '.join(f'{opt} ({count})' for opt, count in duplicates.items())}"
    )


def test_argument_help_is_only_defined_for_arguments() -> None:
    """Only positional arguments should define additional argument help text."""
    for name, (decorator, help_text) in COMMON_OPTIONS.items():
        if help_text is None:
            continue
        click_param = _click_param_from_decorator(decorator)
        assert isinstance(click_param, click.Argument), (
            f"{name} defines shared argument help but is not backed by "
            "click.argument; use click.option(..., help=...) directly for options."
        )
