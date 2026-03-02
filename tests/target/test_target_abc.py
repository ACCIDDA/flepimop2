"""Tests for `TargetABC` and default `WrapperTarget`."""

import numpy as np
import pytest

from flepimop2.target.abc import TargetABC


class DummyTarget(TargetABC):
    """A dummy target for testing purposes."""

    module = "dummy"


@pytest.mark.parametrize("target", [DummyTarget()])
def test_abstraction_error(target: TargetABC) -> None:
    """Test default evaluator raises `NotImplementedError` when not overridden."""
    with pytest.raises(NotImplementedError):
        target.evaluate(
            np.array([1.0, 2.0, 3.0], dtype=np.float64),
            standard=np.array([1.0, 2.0, 3.0], dtype=np.float64)
        )
