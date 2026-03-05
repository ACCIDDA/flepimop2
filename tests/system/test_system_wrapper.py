"""Tests for `SystemABC` and default `WrapperSystem`."""

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from flepimop2.system.abc import build

TEST_SCRIPT = Path(__file__).parent / "system_wrapper_assets" / "dummy_system.py"


@pytest.mark.parametrize("config", [{"script": TEST_SCRIPT, "state_change": "flow"}])
def test_wrapper_system(config: dict[str, Any]) -> None:
    """Test `WrapperSystem` loads a script and uses its `stepper` function."""
    system = build(config)
    result = system.step(
        np.float64(1.0), np.array([1.0, 2.0, 3.0], dtype=np.float64), offset=1.0
    )
    expected = np.array([2.0, 3.0, 4.0], dtype=np.float64)
    np.testing.assert_array_equal(result, expected)


def test_wrapper_system_options_available_via_option_method() -> None:
    """Test `WrapperSystem` exposes configured options through `ModuleABC.option`."""
    system = build({
        "script": TEST_SCRIPT,
        "state_change": "flow",
        "options": {"offset": 1.5},
    })
    assert system.option("offset") == pytest.approx(1.5)
