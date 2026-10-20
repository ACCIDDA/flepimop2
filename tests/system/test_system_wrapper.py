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

from flepimop2._utils._array import coerce_to
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


@pytest.mark.parametrize(
    "config",
    [{"module": "wrapper", "script": TEST_SCRIPT, "state_change": "flow"}],
)
def test_wrapper_system(config: dict[str, Any]) -> None:
    """Test `WrapperSystem` loads a script and uses its `stepper` function."""
    system = build(config)
    time = 1.0
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
        "module": "wrapper",
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
        "module": "wrapper",
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
        1.0,
        np.array([1.0, 2.0], dtype=np.float64),
        beta=ParameterValue(np.array(0.5), ResolvedShape()),
        gamma=ParameterValue(
            np.array([0.2, 0.4], dtype=np.float64),
            ResolvedShape(axis_names=("age",), sizes=(2,)),
        ),
    )
    np.testing.assert_array_equal(result, np.array([1.7, 2.9], dtype=np.float64))


def test_wrapper_system_registers_custom_coercer(tmp_path: Path) -> None:
    """WrapperSystem registers custom coerce_array function when provided."""
    script = tmp_path / "custom_system_script.py"
    script.write_text(
        "import numpy as np\n"
        "ARRAY_BACKEND = 'system_custom_backend'\n"
        "def coerce_array(val):\n"
        "    return np.asarray(val) * 3.0\n"
        "def stepper(time, state, **kwargs):\n"
        "    return state\n"
    )
    system = build({
        "module": "wrapper",
        "script": script,
        "state_change": "flow",
    })
    assert system is not None

    test_input = np.asarray([2.0, 4.0])
    coerced = coerce_to(test_input, "system_custom_backend")
    np.testing.assert_array_equal(coerced, np.asarray([6.0, 12.0]))


@pytest.mark.parametrize(
    "signature",
    [
        "(t, y, beta)",
        "(time, y)",
        "(state, time)",
        "(time)",
        "()",
        "(*args, **kwargs)",
        "(time, *, state)",
    ],
)
def test_wrapper_rejects_invalid_runtime_argument_names(
    tmp_path: Path, signature: str
) -> None:
    """Invalid runtime signatures fail before model parameter lookup."""
    script = tmp_path / "invalid_signature.py"
    script.write_text(f"def stepper{signature}:\n    return None\n")
    with pytest.raises(
        ValueError, match=r"first two arguments must be named.*time.*state"
    ):
        build({"module": "wrapper", "script": script, "state_change": "flow"})


@pytest.mark.parametrize("positional_only", [False, True])
def test_wrapper_accepts_positional_runtime_arguments(
    tmp_path: Path, *, positional_only: bool
) -> None:
    """Named and positional-only runtime inputs retain default model parameters."""
    signature = (
        "(time, state, /, offset=2.0)"
        if positional_only
        else "(time, state, offset=2.0)"
    )
    script = tmp_path / "valid_signature.py"
    script.write_text(f"def stepper{signature}:\n    return state + offset\n")
    system = build({"module": "wrapper", "script": script, "state_change": "flow"})
    assert set(system.requested_parameters(AxisCollection())) == {"offset"}
    result = system.step(np.float64(0), np.array([1.0, 3.0]))
    np.testing.assert_array_equal(result, [3.0, 5.0])
