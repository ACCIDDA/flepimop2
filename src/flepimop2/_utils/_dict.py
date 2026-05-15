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
"""Private dictionary helpers."""

from copy import deepcopy
from typing import Any


def _deep_merge_dicts(current: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """
    Deep-merge two dictionaries, preferring values from `patch`.

    Only nested dictionaries are merged recursively. Lists and scalars are
    replaced wholesale by the incoming patch value.

    Args:
        current: The current dictionary.
        patch: The incoming patch dictionary.

    Returns:
        A merged dictionary.

    Examples:
        >>> _deep_merge_dicts({"alpha": 1}, {"beta": 2})
        {'alpha': 1, 'beta': 2}
        >>> _deep_merge_dicts(
        ...     {"outer": {"left": 1, "shared": {"x": 1, "z": True}}},
        ...     {"outer": {"right": 2, "shared": {"y": 2, "z": False}}},
        ... )
        {'outer': {'left': 1, 'shared': {'x': 1, 'z': False, 'y': 2}, 'right': 2}}
        >>> _deep_merge_dicts({"values": [1, 2, 3]}, {"values": [4, 5]})
        {'values': [4, 5]}
        >>> current = {"outer": {"left": 1}}
        >>> merged = _deep_merge_dicts(current, {"outer": {"right": 2}})
        >>> current
        {'outer': {'left': 1}}
        >>> merged
        {'outer': {'left': 1, 'right': 2}}
    """
    merged = deepcopy(current)
    for key, patch_value in patch.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(patch_value, dict)
        ):
            merged[key] = _deep_merge_dicts(merged[key], patch_value)
        else:
            merged[key] = deepcopy(patch_value)
    return merged
