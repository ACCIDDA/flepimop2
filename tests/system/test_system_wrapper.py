"""Tests for `SystemABC` and default `WrapperSystem`."""

from pathlib import Path
from typing import Any

import numpy as np
import pytest

import flepimop2.system as system_module
from flepimop2.system import SystemABC

TEST_SCRIPT = Path(__file__).with_suffix("") / "dummy_system.py"


@pytest.mark.parametrize("system", [SystemABC()])
def test_abstraction_error(system: SystemABC) -> None:
    """Test `SystemABC` raises `NotImplementedError` when not overridden."""
    with pytest.raises(NotImplementedError):
        system.step(0.0, np.array([1.0, 2.0, 3.0], dtype=np.float64))


@pytest.mark.parametrize("config", [{"script": TEST_SCRIPT}])
def test_wrapper_system(config: dict[str, Any]) -> None:
    """Test `WrapperSystem` loads a script and uses its `stepper` function."""
    system = system_module.build(config)
    result = system.stepper(
        1.0, np.array([1.0, 2.0, 3.0], dtype=np.float64), offset=1.0
    )
    expected = np.array([2.0, 3.0, 4.0], dtype=np.float64)
    np.testing.assert_array_equal(result, expected)
