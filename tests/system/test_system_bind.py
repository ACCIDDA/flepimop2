"""Tests `SystemABC` ability to bind static parameters."""

from pathlib import Path

import pytest

from flepimop2.system.abc import SystemABC, build
from flepimop2.typing import StateChangeEnum
from flepimop2.exceptions import Flepimop2ValidationError

TEST_SCRIPT = Path(__file__).parent / "dummy_system.py"
system = build({"script": TEST_SCRIPT, "state_change": StateChangeEnum.DELTA})

@pytest.mark.parametrize("test_system", [system])
def test_set_valid_static_parameters(test_system: SystemABC):
    """Confirm no errors when setting all valid parameters."""
    test_system.bind(offset = 5.0)

@pytest.mark.parametrize("test_system", [system])
def test_set_valid_static_parameters_dict_version(test_system: SystemABC):
    """Confirm no errors when setting all valid parameters."""
    test_system.bind(params={"offset": 5.0})


@pytest.mark.parametrize("test_system", [system])
def test_set_static_parameter_throws_error_on_fixed_time(test_system: SystemABC):
    """Confirm error thrown when attempting to fix time parameter."""
    with pytest.raises(Flepimop2ValidationError):
        test_system.bind(time = 100)

@pytest.mark.parametrize("test_system", [system])
def test_set_static_parameter_throws_error_on_fixed_state(test_system: SystemABC):
    """Confirm error thrown when attempting to fix state parameter."""
    with pytest.raises(Flepimop2ValidationError):
        test_system.bind(state = [1.0, 2.0, 3.0])

@pytest.mark.parametrize("test_system", [system])
def test_set_nonexistent_parameter_throws_error(test_system: SystemABC):
    """Confirm error thrown when setting a parameter that does not exist."""
    with pytest.raises(Flepimop2ValidationError):
        test_system.bind(nonexistent_param = 5.0)


@pytest.mark.parametrize("test_system", [system])
def test_set_parameter_with_invalid_type_throws_error(test_system: SystemABC):
    """Confirm error thrown when setting parameter with invalid type."""
    with pytest.raises(Flepimop2ValidationError):
        test_system.bind(offset = "invalid_string")