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


def test_wrapper_system_options_available_via_option_method() -> None:
    """Test `WrapperSystem` exposes configured options through `ModuleABC.option`."""
    system = build({
        "script": TEST_SCRIPT,
        "state_change": "flow",
        "options": {"offset": 1.5},
    })
    assert system.option("offset") == pytest.approx(1.5)


def test_wrapper_system_loads_requested_parameters_and_model_state() -> None:
    """Wrapper systems should expose requested parameter and state metadata."""
    system = build({"script": WRAPPER_SCRIPT_WITH_EXTRAS, "state_change": "flow"})
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
