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

from flepimop2._cli._options import COMMON_OPTIONS


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
    for decorator in COMMON_OPTIONS.values():
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
