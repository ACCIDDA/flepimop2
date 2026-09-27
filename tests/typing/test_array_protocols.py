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
"""Static and runtime fixtures for backend-neutral callable protocols."""

from collections.abc import Mapping
from typing import Any

import numpy as np

from flepimop2.engine.abc import EngineProtocol
from flepimop2.parameter.abc import ModelStateSpecification, ParameterValue
from flepimop2.typing import (
    Array,
    Float64NDArray,
    IdentifierString,
    SystemProtocol,
)


class _FakeArray:
    """Small non-NumPy object satisfying the public `Array` protocol."""

    @property
    def shape(self) -> tuple[int, ...]:
        """Return the fixture shape."""
        return (1,)

    @property
    def dtype(self) -> object:
        """Return the fixture dtype marker."""
        return float

    def item(self) -> float:
        """Return the fixture scalar."""
        return 1.0


def _fake_step(
    time: np.float64,
    state: Array,
    **kwargs: Any,
) -> Array:
    """Return the input state without requiring a NumPy array."""
    del time, kwargs
    return state


def _fake_runner(
    stepper: SystemProtocol,
    times: Float64NDArray,
    initial_state: dict[IdentifierString, ParameterValue],
    params: Mapping[IdentifierString, ParameterValue],
    model_state: ModelStateSpecification | None = None,
    **kwargs: Any,
) -> Array:
    """Return a non-NumPy result through the engine callable contract."""
    del times, initial_state, params, model_state, kwargs
    return stepper(np.float64(0.0), _FakeArray())


_FAKE_SYSTEM: SystemProtocol = _fake_step
_FAKE_ENGINE: EngineProtocol = _fake_runner


def test_callable_protocols_accept_non_numpy_array() -> None:
    """System and engine protocols should preserve a non-NumPy array object."""
    fake = _FakeArray()

    assert isinstance(fake, Array)
    assert _FAKE_SYSTEM(np.float64(0.0), fake) is fake
    result = _FAKE_ENGINE(_FAKE_SYSTEM, np.array([0.0]), {}, {})
    assert isinstance(result, _FakeArray)
