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
"""Tests for `SystemABC` and default `WrapperSystem`."""

from pathlib import Path
from typing import Any, Final

import numpy as np
import pytest

from flepimop2.axis import AxisCollection, ResolvedShape
from flepimop2.parameter.abc import (
    ModelStateSpecification,
    ParameterRequest,
    ParameterValue,
)
from flepimop2.system.abc import build

TEST_SCRIPT: Final = Path(__file__).parent / "system_wrapper_assets" / "dummy_system.py"
WRAPPER_SCRIPT_WITH_EXTRAS: Final = (
    Path(__file__).parent / "system_wrapper_assets" / "wrapper_system_with_extras.py"
)


@pytest.mark.parametrize("config", [{"script": TEST_SCRIPT, "state_change": "flow"}])
def test_wrapper_system(config: dict[str, Any]) -> None:
    """Test `WrapperSystem` loads a script and uses its `stepper` function."""
    system = build(config)
    time = np.float64(1.0)
    offset = ParameterValue(np.array(1.0), ResolvedShape())
    init_state = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    result = system.step(time, init_state, offset=offset)
    expected = init_state + offset.item()
    np.testing.assert_array_equal(result, expected)
    axes = AxisCollection()
    assert system.requested_parameters(axes) == {
        "offset": ParameterRequest(name="offset"),
    }
    assert system.model_state(axes) is None


def test_wrapper_system_options_available_via_option_method() -> None:
    """Test `WrapperSystem` exposes configured options through `ModuleABC.option`."""
    system = build({
        "script": TEST_SCRIPT,
        "state_change": "flow",
        "options": {"offset": 1.5},
    })
    assert system.option("offset") == pytest.approx(1.5)


def test_wrapper_system_loads_requested_parameters_and_model_state_from_config() -> (
    None
):
    """Wrapper systems should expose parameter and state metadata from config."""
    system = build({
        "script": WRAPPER_SCRIPT_WITH_EXTRAS,
        "state_change": "flow",
        "requested_parameters": {
            "beta": None,
            "gamma": {
                "axes": ["age"],
                "broadcast": True,
            },
        },
        "model_state": {
            "parameter_names": ["s0", "i0", "r0"],
            "axes": ["age"],
            "broadcast": True,
            "labels": ["S", "I", "R"],
        },
    })
    axes = AxisCollection.from_config({
        "age": {"kind": "categorical", "labels": ["0-17", "18-64"]}
    })

    assert system.requested_parameters(axes) == {
        "beta": ParameterRequest(name="beta"),
        "gamma": ParameterRequest(
            name="gamma",
            axes=("age",),
            broadcast=True,
        ),
    }
    assert system.model_state(axes) == ModelStateSpecification(
        parameter_names=("s0", "i0", "r0"),
        axes=("age",),
        broadcast=True,
        labels=("S", "I", "R"),
    )
    result = system.step(
        np.float64(1.0),
        np.array([1.0, 2.0], dtype=np.float64),
        beta=ParameterValue(np.array(0.5), ResolvedShape()),
        gamma=ParameterValue(
            np.array([0.2, 0.4], dtype=np.float64),
            ResolvedShape(axis_names=("age",), sizes=(2,)),
        ),
    )
    np.testing.assert_array_equal(result, np.array([1.7, 2.9], dtype=np.float64))
