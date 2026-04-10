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
