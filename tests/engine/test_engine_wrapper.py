"""Tests for `EngineABC` and default `WrapperEngine`."""

from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

import flepimop2.engine as engine_module
import flepimop2.system as system_module
from flepimop2.system import SystemABC

TEST_SCRIPT = Path(__file__).with_suffix("") / "dummy_engine.py"


def _test_step(
    time: np.float64, state: NDArray[np.float64], offset: float
) -> NDArray[np.float64]:
    return (state + offset) * time


@pytest.mark.parametrize("config", [{"script": TEST_SCRIPT}])
@pytest.mark.parametrize("system", [system_module.build(_test_step)])
@pytest.mark.parametrize("params", [{"offset": 1.0}])
def test_wrapper_system(
    config: dict, system: SystemABC, params: dict[str, float]
) -> None:
    """Test `WrapperEngine` loads a script and uses its `runner` function."""
    engine = engine_module.build(config)
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
