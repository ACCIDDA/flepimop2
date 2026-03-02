"""Tests for `TargetABC` and default `WrapperTarget`."""

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from flepimop2.system.abc import build

TEST_SCRIPT = Path(__file__).with_suffix("") / "dummy_target.py"


@pytest.mark.parametrize("config", [{"script": TEST_SCRIPT}])
def test_wrapper_target(config: dict[str, Any]) -> None:
    """Test `WrapperTarget` loads a script and uses its `evaluator` function."""
    target = build(config)
    result = target.evaluate(
        np.array([1.0, 2.0, 3.0], dtype=np.float64),
        standard=np.array([2.0, 3.0, 4.0], dtype=np.float64)
    )
    expected = np.array([1.0], dtype=np.float64)  # RMSE of off-by [1,1,1] = 1.0
    np.testing.assert_array_equal(result, expected)
