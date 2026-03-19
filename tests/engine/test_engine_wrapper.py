"""Tests for `EngineABC` and default `WrapperEngine`."""

from pathlib import Path
from typing import Any, Final

import numpy as np
import pytest

from flepimop2.axis import ResolvedShape
from flepimop2.engine.abc import build as engine_build
from flepimop2.exceptions import ValidationIssue
from flepimop2.parameter.abc import ModelStateSpecification, ParameterValue
from flepimop2.system.abc import SystemABC
from flepimop2.system.abc import build as system_build
from flepimop2.system.wrapper import WrapperSystem
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
    "config", [{"script": TEST_ENGINE_SCRIPT, "state_change": "flow"}]
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
    "config", [{"script": TEST_ENGINE_SCRIPT, "state_change": "flow"}]
)
def test_wrapper_engine_validate_system_properties(config: dict[str, Any]) -> None:
    """Test `WrapperEngine` validates system properties compatibility."""
    engine = engine_build(config)

    compatible_system = WrapperSystem(
        script=TEST_SYSTEM_SCRIPT, state_change=StateChangeEnum.FLOW
    )
    assert engine.validate_system(compatible_system) is None

    incompatible_system = WrapperSystem(
        script=TEST_SYSTEM_SCRIPT, state_change=StateChangeEnum.DELTA
    )
    issues = engine.validate_system(incompatible_system)
    assert issues is not None
    assert all(isinstance(issue, ValidationIssue) for issue in issues)
    assert [issue.kind for issue in issues] == ["incompatible_system"]
