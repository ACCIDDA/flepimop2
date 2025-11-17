"""Tests for `SystemABC` and default `WrapperSystem`."""

from typing import Literal

import numpy as np
import pytest

from flepimop2.system.system_base import SystemABC


class DummySystem(SystemABC):
    """A dummy system for testing purposes."""

    module: Literal["dummy"] = "dummy"


@pytest.mark.parametrize("system", [DummySystem()])
def test_abstraction_error(system: SystemABC) -> None:
    """Test default stepper raises `NotImplementedError` when not overridden."""
    with pytest.raises(NotImplementedError):
        system.step(np.float64(0.0), np.array([1.0, 2.0, 3.0], dtype=np.float64))
