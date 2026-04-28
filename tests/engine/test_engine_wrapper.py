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
"""Tests for `EngineABC` and default `WrapperEngine`."""

from pathlib import Path
from typing import Any, Final

import numpy as np
import pytest

from flepimop2.axis import ResolvedShape
from flepimop2.engine.abc import build as engine_build
from flepimop2.exceptions import ValidationIssue
from flepimop2.parameter.abc import ParameterValue
from flepimop2.system.abc import SystemABC
from flepimop2.system.abc import build as system_build
from flepimop2.typing import StateChangeEnum

TEST_ENGINE_SCRIPT: Final = (
    Path(__file__).parent / "engine_wrapper_assets" / "dummy_engine.py"
)
TEST_SYSTEM_SCRIPT: Final = (
    Path(__file__).parent.parent
    / "system"
    / "system_wrapper_assets"
    / "dummy_system.py"
).absolute()


@pytest.mark.parametrize(
    "config", [{"script": TEST_ENGINE_SCRIPT, "state_change": "flow"}]
)
@pytest.mark.parametrize(
    "system",
    [
        system_build({
            "module": "flepimop2.system.wrapper",
            "script": TEST_SYSTEM_SCRIPT,
            "state_change": "flow",
        })
    ],
)
@pytest.mark.parametrize(
    "params", [{"offset": ParameterValue(np.array(1.0), ResolvedShape())}]
)
def test_wrapper_system(
    config: dict[str, Any],
    system: SystemABC,
    params: dict[str, ParameterValue],
) -> None:
    """Test `WrapperEngine` loads a script and uses its `runner` function."""
    engine = engine_build(config)
    result = engine.run(
        system,
        np.array([1.0, 2.0], dtype=np.float64),
        np.array([1.0, 2.0], dtype=np.float64),
        params,
        accumulate=False,
    )
    expected = np.zeros((2, 3), dtype=np.float64)
    expected[:, 0] = [1.0, 2.0]
    expected[0, 1:] = [1.0, 2.0]
    expected[1, 1:] = (expected[0, 1:] + params["offset"].item()) * 2.0
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize(
    "config", [{"script": TEST_ENGINE_SCRIPT, "state_change": "flow"}]
)
def test_wrapper_engine_validate_system_properties(config: dict[str, Any]) -> None:
    """Test `WrapperEngine` validates system properties compatibility."""
    engine = engine_build(config)

    compatible_system = system_build({
        "script": TEST_SYSTEM_SCRIPT,
        "state_change": StateChangeEnum.FLOW,
    })
    assert engine.validate_system(compatible_system) is None

    incompatible_system = system_build({
        "script": TEST_SYSTEM_SCRIPT,
        "state_change": StateChangeEnum.DELTA,
    })
    issues = engine.validate_system(incompatible_system)
    assert issues is not None
    assert all(isinstance(issue, ValidationIssue) for issue in issues)
    assert [issue.kind for issue in issues] == ["incompatible_system"]
