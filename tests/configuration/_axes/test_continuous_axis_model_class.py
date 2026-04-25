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
"""Unit tests for the `ContinuousAxisModel` class."""

from typing import Literal

import pytest
from pydantic import ValidationError

from flepimop2.configuration._axes import ContinuousAxisModel


@pytest.mark.parametrize(
    ("domain", "size", "spacing"),
    [
        ((0.0, 1.0), 2, "linear"),
        ((1.0, 100.0), 5, "log"),
        ((0.0, 12.0), 20, "linear"),
    ],
)
def test_continuous_axis_model_valid(
    domain: tuple[float, float], size: int, spacing: Literal["linear", "log"]
) -> None:
    """Test that valid continuous axis configurations are accepted."""
    m = ContinuousAxisModel(domain=domain, size=size, spacing=spacing)
    assert m.kind == "continuous"
    assert m.domain == domain
    assert m.size == size
    assert m.spacing == spacing


def test_continuous_axis_model_default_spacing() -> None:
    """Test that spacing defaults to 'linear'."""
    m = ContinuousAxisModel(domain=(0.0, 1.0), size=2)
    assert m.spacing == "linear"


@pytest.mark.parametrize(
    ("domain", "size", "spacing"),
    [
        ((5.0, 0.0), 3, "linear"),  # reversed domain
        ((1.0, 1.0), 3, "linear"),  # equal bounds
        ((0.0, 1.0), 1, "linear"),  # size not > 1
        ((0.0, 10.0), 3, "log"),  # log with non-positive lower bound
        ((-1.0, 10.0), 3, "log"),  # log with negative lower bound
    ],
)
def test_continuous_axis_model_invalid(
    domain: tuple[float, float], size: int, spacing: Literal["linear", "log"]
) -> None:
    """Test that invalid continuous axis configurations raise ValidationError."""
    with pytest.raises(ValidationError):
        ContinuousAxisModel(domain=domain, size=size, spacing=spacing)
