"""Tests for `EngineABC` and default `WrapperEngine`."""

from pathlib import Path
from typing import Final

import numpy as np
import pytest

from flepimop2.engine.abc import build as engine_build
from flepimop2.exceptions import ValidationIssue
from flepimop2.system.abc import SystemABC
from flepimop2.system.abc import build as system_build
from flepimop2.system.wrapper import WrapperSystem
from flepimop2.typing import StateChangeEnum

TEST_ENGINE_SCRIPT: Final = Path(__file__).with_suffix("") / "dummy_engine.py"
TEST_SYSTEM_SCRIPT: Final = (
    Path(__file__).parent.parent / "system" / "test_system_wrapper" / "dummy_system.py"
).absolute()


@pytest.mark.parametrize("config", [{"script": TEST_ENGINE_SCRIPT}])
@pytest.mark.parametrize(
    "system",
    [
        system_build({
            "module": "flepimop2.system.wrapper",
            "script": TEST_SYSTEM_SCRIPT,
        })
    ],
)
@pytest.mark.parametrize("params", [{"offset": 1.0}])
def test_wrapper_system(
    config: dict, system: SystemABC, params: dict[str, float]
) -> None:
    """Test `WrapperEngine` loads a script and uses its `runner` function."""
    engine = engine_build(config)
    result = engine.run(
        system,
        [1.0, 2.0],
        np.array([1.0, 2.0], dtype=np.float64),
        params,
        accumulate=False,
    )
    expected = np.zeros((2, 3), dtype=np.float64)
    expected[:, 0] = [1.0, 2.0]
    expected[0, 1:] = [1.0, 2.0]
    expected[1, 1:] = (expected[0, 1:] + params["offset"]) * 2.0
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize("config", [{"script": TEST_ENGINE_SCRIPT}])
def test_wrapper_engine_validate_system_properties(config: dict) -> None:
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
