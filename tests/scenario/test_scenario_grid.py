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
"""Tests `ScenarioABC` grid implementation."""

import itertools
from typing import Any

import pytest

from flepimop2.scenario.abc import build as scenario_build
from flepimop2.typing import IdentifierString


@pytest.mark.parametrize(
    "params",
    [{"param1": [1, 2], "param2": ["a", "b"]}, {"param1": [1], "param2": ["a"]}],
)
def test_set_valid_static_parameters(params: dict[IdentifierString, Any]) -> None:
    """Confirm generation of all combinations of parameters."""
    scenario = scenario_build({"parameters": params})
    expected_scenarios = list(itertools.product(*params.values()))
    assert list(scenario.scenarios()) == expected_scenarios
