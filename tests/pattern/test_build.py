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
"""Tests for the `flepimop2.pattern.abc.build` function."""

import pytest

from flepimop2.pattern.abc import PatternABC, build
from flepimop2.pattern.default import DefaultPattern


def test_build_resolves_default_short_name() -> None:
    """A short `module` name resolves under the `pattern` namespace."""
    pattern = build({"module": "default"})
    assert isinstance(pattern, DefaultPattern)
    assert isinstance(pattern, PatternABC)
    assert pattern.module == "flepimop2.pattern.default"


def test_build_accepts_fully_qualified_name() -> None:
    """A fully-qualified `module` name builds the same module."""
    pattern = build({"module": "flepimop2.pattern.default"})
    assert isinstance(pattern, DefaultPattern)


def test_build_rejects_missing_module() -> None:
    """A configuration without a `module` is rejected."""
    with pytest.raises(ValueError, match="must define a non-empty"):
        build({})
