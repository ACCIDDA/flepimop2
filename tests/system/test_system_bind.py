"""Tests `SystemABC` ability to bind static parameters."""

from pathlib import Path

import numpy as np
import pytest

from flepimop2.system.abc import SystemABC, build
from flepimop2.typing import StateChangeEnum

TEST_SCRIPT = Path(__file__).parent / "dummy_system.py"
system = build({"script": TEST_SCRIPT, "state_change": StateChangeEnum.DELTA})

testpar = pytest.mark.parametrize("test_system", [system])


@testpar
def test_set_valid_static_parameters(test_system: SystemABC) -> None:
    """Confirm no errors when setting all valid parameters."""
    offset = 5.0
    time = np.float64(1.0)
    initial_state = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    newproto = test_system.bind(offset=offset)
    assert all(newproto(time, initial_state) == (initial_state + offset))
    newproto = test_system.bind(params={"offset": offset * 2})
    assert all(newproto(time, initial_state) == (initial_state + offset * 2))


@testpar
def test_set_static_parameter_throws_error_on_fixed_state(
    test_system: SystemABC,
) -> None:
    """Confirm error thrown when attempting to fix state parameter."""
    with pytest.raises(TypeError):
        test_system.bind(time=100)
    with pytest.raises(TypeError):
        test_system.bind(state=[1.0, 2.0, 3.0])
    with pytest.raises(TypeError):
        test_system.bind(nonexistent_param=5.0)
    with pytest.raises(TypeError):
        test_system.bind(offset="invalid_string")
