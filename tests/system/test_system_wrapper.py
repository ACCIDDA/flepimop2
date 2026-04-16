# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
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
    time = np.float64(1.0)
    offset = 1.0
    init_state = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    result = system.step(time, init_state, offset=offset)
    expected = init_state + offset
    np.testing.assert_array_equal(result, expected)


def test_wrapper_system_options_available_via_option_method() -> None:
    """Test `WrapperSystem` exposes configured options through `ModuleABC.option`."""
    system = build({
        "script": TEST_SCRIPT,
        "state_change": "flow",
        "options": {"offset": 1.5},
    })
    assert system.option("offset") == pytest.approx(1.5)
