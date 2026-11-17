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
"""Tests for `ModelStateSpecification` runtime behavior."""

import pytest

from flepimop2.parameter.abc import ModelStateSpecification


def test_model_state_specification_select_by_parameter_name() -> None:
    """select() retains only requested parameter names and matching labels."""
    spec = ModelStateSpecification(
        parameter_names=("s0", "e0", "i0", "r0"),
        labels=("S", "E", "I", "R"),
    )

    sub = spec.select("i0", "r0")
    assert sub.parameter_names == ("i0", "r0")
    assert sub.labels == ("I", "R")


def test_model_state_specification_select_by_label() -> None:
    """select() accepts human-readable labels and maps them to parameter names."""
    spec = ModelStateSpecification(
        parameter_names=("s0", "e0", "i0", "r0"),
        labels=("S", "E", "I", "R"),
    )

    sub = spec.select("S", "I")
    assert sub.parameter_names == ("s0", "i0")
    assert sub.labels == ("S", "I")


def test_model_state_specification_select_without_labels() -> None:
    """select() works on specifications without labels."""
    spec = ModelStateSpecification(parameter_names=("x0", "y0"))
    sub = spec.select("y0")
    assert sub.parameter_names == ("y0",)
    assert sub.labels is None


def test_model_state_specification_select_empty_returns_self() -> None:
    """select() with no names returns the same specification."""
    spec = ModelStateSpecification(parameter_names=("x0",))
    assert spec.select() is spec


def test_model_state_specification_select_unknown_name_raises() -> None:
    """select() raises ValueError when given an unknown name."""
    spec = ModelStateSpecification(parameter_names=("s0", "i0"))
    with pytest.raises(
        ValueError, match="Unknown model state parameter or label 'bad'"
    ):
        spec.select("bad")


def test_model_state_specification_filter_factory() -> None:
    """filter() constructs a ModelStateSpecification from names."""
    spec = ModelStateSpecification.filter("s0", "i0", labels=("S", "I"))
    assert spec.parameter_names == ("s0", "i0")
    assert spec.labels == ("S", "I")
