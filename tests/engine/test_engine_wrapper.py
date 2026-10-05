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
"""Tests for `EngineABC` and default `WrapperEngine`."""

from pathlib import Path
from typing import Any, Final

import numpy as np
import pytest

from flepimop2._utils._array import coerce_to
from flepimop2.axis import ResolvedShape
from flepimop2.engine.abc import build as engine_build
from flepimop2.exceptions import ValidationIssue
from flepimop2.parameter.abc import ModelStateSpecification, ParameterValue
from flepimop2.system.abc import SystemABC
from flepimop2.system.abc import build as system_build
from flepimop2.typing import StateChangeEnum

TEST_ENGINE_SCRIPT: Final = (
    Path(__file__).parent / "engine_wrapper_assets" / "dummy_engine.py"
)
TEST_SYSTEM_SCRIPT: Final = (
    Path(__file__).parent.parent
    / "system"
    / "system_wrapper_assets"
    / "dummy_system.py"
).absolute()


@pytest.mark.parametrize(
    "config",
    [{"module": "wrapper", "script": TEST_ENGINE_SCRIPT, "state_change": "flow"}],
)
@pytest.mark.parametrize(
    "system",
    [
        system_build({
            "module": "flepimop2.system.wrapper",
            "script": TEST_SYSTEM_SCRIPT,
            "state_change": "flow",
        })
    ],
)
@pytest.mark.parametrize(
    "params", [{"offset": ParameterValue(np.array(1.0), ResolvedShape())}]
)
def test_wrapper_system(
    config: dict[str, Any],
    system: SystemABC,
    params: dict[str, ParameterValue],
) -> None:
    """Test `WrapperEngine` loads a script and uses its `runner` function."""
    engine = engine_build(config)
    result = engine.run(
        system,
        np.array([1.0, 2.0], dtype=np.float64),
        {
            "x0": ParameterValue(np.array(1.0), ResolvedShape()),
            "x1": ParameterValue(np.array(2.0), ResolvedShape()),
        },
        params,
        model_state=ModelStateSpecification(parameter_names=("x0", "x1")),
        accumulate=False,
    )
    expected = np.zeros((2, 3), dtype=np.float64)
    expected[:, 0] = [1.0, 2.0]
    expected[0, 1:] = [1.0, 2.0]
    expected[1, 1:] = (expected[0, 1:] + params["offset"].item()) * 2.0
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize(
    "config",
    [{"module": "wrapper", "script": TEST_ENGINE_SCRIPT, "state_change": "flow"}],
)
def test_wrapper_engine_validate_system_properties(config: dict[str, Any]) -> None:
    """Test `WrapperEngine` validates system properties compatibility."""
    engine = engine_build(config)

    compatible_system = system_build({
        "module": "wrapper",
        "script": TEST_SYSTEM_SCRIPT,
        "state_change": StateChangeEnum.FLOW,
    })
    assert engine.validate_system(compatible_system) is None

    incompatible_system = system_build({
        "module": "wrapper",
        "script": TEST_SYSTEM_SCRIPT,
        "state_change": StateChangeEnum.DELTA,
    })
    issues = engine.validate_system(incompatible_system)
    assert issues is not None
    assert all(isinstance(issue, ValidationIssue) for issue in issues)
    assert [issue.kind for issue in issues] == ["incompatible_system"]


def test_wrapper_engine_registers_array_backend(tmp_path: Path) -> None:
    """WrapperEngine inspects ARRAY_BACKEND from the wrapped script."""
    script = tmp_path / "custom_backend_engine.py"
    script.write_text(
        "ARRAY_BACKEND = 'jax'\n"
        "def runner(stepper, times, initial_state, params, **kwargs):\n"
        "    return times\n"
    )
    engine = engine_build({
        "module": "wrapper",
        "script": script,
        "state_change": "flow",
    })
    assert engine.backend == "jax"


def test_wrapper_engine_registers_custom_coercer(tmp_path: Path) -> None:
    """WrapperEngine registers custom coerce_array function when provided."""
    script = tmp_path / "custom_coercer_engine.py"
    script.write_text(
        "import numpy as np\n"
        "ARRAY_BACKEND = 'scaled_numpy'\n"
        "def coerce_array(val):\n"
        "    return np.asarray(val) * 10.0\n"
        "def runner(stepper, times, initial_state, params, **kwargs):\n"
        "    return times\n"
    )
    engine = engine_build({
        "module": "wrapper",
        "script": script,
        "state_change": "flow",
    })
    assert engine.backend == "scaled_numpy"

    test_input = np.asarray([1.0, 2.0])
    coerced = coerce_to(test_input, "scaled_numpy")
    np.testing.assert_array_equal(coerced, np.asarray([10.0, 20.0]))
