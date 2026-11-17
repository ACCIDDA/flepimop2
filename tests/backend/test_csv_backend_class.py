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
"""Unit tests for the `CsvBackend` class."""

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from flepimop2.axis import AxisCollection
from flepimop2.backend.abc import build
from flepimop2.backend.csv import CsvBackend
from flepimop2.meta import RunMeta
from flepimop2.parameter.abc import ModelStateSpecification
from flepimop2.typing import Float64NDArray, _TaggedArray


@pytest.mark.parametrize(
    ("sample_array", "run_meta"),
    [
        (
            np.array([[1.0, 2.0], [3.0, 4.0]]),
            RunMeta(
                action="simulate",
                timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
                name="array_test",
            ),
        ),
        (
            np.array([[0.0]]),
            RunMeta(
                action="simulate",
                timestamp=datetime(2024, 6, 15, 8, 45, 0, tzinfo=UTC),
                name=None,
            ),
        ),
    ],
)
def test_csv_backend_save_and_read_round_trip(
    tmp_path: Path,
    sample_array: Float64NDArray,
    run_meta: RunMeta,
) -> None:
    """Test that saving and reading an array returns the same data."""
    backend = build({"module": "flepimop2.backend.csv", "root": str(tmp_path)})

    backend.save(sample_array, run_meta)
    loaded_array = backend.read(run_meta)

    assert_array_equal(loaded_array, sample_array)


def test_csv_backend_save_and_read_long_format_round_trip(tmp_path: Path) -> None:
    """A long-format CSV is written when model_state and axes are provided."""
    backend = CsvBackend(root=tmp_path)
    run_meta = RunMeta(name="long_test")
    # 2 time points x (2 states x 2 age positions = 4 columns)
    data = np.array([[100.0, 50.0, 1.0, 2.0], [90.0, 45.0, 2.0, 3.0]])
    model_state = ModelStateSpecification(parameter_names=("s0", "i0"), axes=("age",))
    axes = AxisCollection.from_config({
        "age": {"kind": "categorical", "labels": ["young", "old"]},
    })

    backend.save(data, run_meta, model_state=model_state, axes=axes)

    file_path = backend._get_file_path(run_meta)
    lines = file_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "time,state,age,value"
    assert lines[1] == "0,s0,young,100.0"
    assert lines[2] == "0,s0,old,50.0"
    assert lines[3] == "0,i0,young,1.0"
    assert lines[4] == "0,i0,old,2.0"
    assert lines[5] == "1,s0,young,90.0"

    loaded = backend.read(run_meta)
    assert isinstance(loaded, _TaggedArray)
    assert loaded.dims == ("time", "state", "age")
    assert loaded.coords["state"] == ("s0", "i0")
    assert loaded.coords["age"] == ("young", "old")
    assert loaded.shape == (2, 2, 2)
    assert_array_equal(loaded[0, 0, :], np.array([100.0, 50.0]))
    assert_array_equal(loaded[1, 1, :], np.array([2.0, 3.0]))


def test_csv_backend_save_with_leading_time_column(tmp_path: Path) -> None:
    """A leading time column is preserved as the time coordinate values."""
    backend = CsvBackend(root=tmp_path)
    run_meta = RunMeta(name="time_col_test")
    # Column 0 is time (0.0, 1.5); columns 1-2 are states s0, i0
    data = np.array([[0.0, 100.0, 1.0], [1.5, 95.0, 2.0]])
    model_state = ModelStateSpecification(parameter_names=("s0", "i0"))

    backend.save(data, run_meta, model_state=model_state)

    file_path = backend._get_file_path(run_meta)
    lines = file_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "time,state,value"
    assert lines[1] == "0.0,s0,100.0"
    assert lines[3] == "1.5,s0,95.0"

    loaded = backend.read(run_meta)
    assert isinstance(loaded, _TaggedArray)
    assert loaded.dims == ("time", "state")
    assert loaded.coords["time"] == ("0.0", "1.5")
    assert loaded.coords["state"] == ("s0", "i0")
    assert_array_equal(np.asarray(loaded), np.array([[100.0, 1.0], [95.0, 2.0]]))


def test_csv_backend_read_with_filtering(tmp_path: Path) -> None:
    """Reading with filter selects only matching rows and reconstructs grid."""
    backend = CsvBackend(root=tmp_path)
    run_meta = RunMeta(name="filter_test")
    data = np.array([[100.0, 50.0, 1.0, 2.0], [90.0, 45.0, 2.0, 3.0]])
    model_state = ModelStateSpecification(parameter_names=("s0", "i0"), axes=("age",))
    axes = AxisCollection.from_config({
        "age": {"kind": "categorical", "labels": ["young", "old"]},
    })

    backend.save(data, run_meta, model_state=model_state, axes=axes)

    # Filter to only state "i0"
    filtered_state = backend.read(run_meta, filters={"state": "i0"})
    assert isinstance(filtered_state, _TaggedArray)
    assert filtered_state.dims == ("time", "state", "age")
    assert filtered_state.coords["state"] == ("i0",)
    assert filtered_state.shape == (2, 1, 2)
    assert_array_equal(filtered_state[:, 0, :], np.array([[1.0, 2.0], [2.0, 3.0]]))

    # Filter to only age "young"
    filtered_age = backend.read(run_meta, filters={"age": "young"})
    assert isinstance(filtered_age, _TaggedArray)
    assert filtered_age.coords["age"] == ("young",)
    assert filtered_age.shape == (2, 2, 1)
    assert_array_equal(filtered_age[:, :, 0], np.array([[100.0, 1.0], [90.0, 2.0]]))


def test_csv_backend_fallback_on_unaligned_shape(tmp_path: Path) -> None:
    """Data with mismatched shape falls back to plain matrix format."""
    backend = CsvBackend(root=tmp_path)
    run_meta = RunMeta(name="mismatch_test")
    # model_state expects 4 columns (2 states x 2 ages), but data has only 3
    data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    model_state = ModelStateSpecification(parameter_names=("s0", "i0"), axes=("age",))
    axes = AxisCollection.from_config({
        "age": {"kind": "categorical", "labels": ["young", "old"]},
    })

    backend.save(data, run_meta, model_state=model_state, axes=axes)

    file_path = backend._get_file_path(run_meta)
    first_line = file_path.read_text(encoding="utf-8").splitlines()[0]
    # No header: raw numbers
    assert (
        first_line
        == "1.000000000000000000e+00,2.000000000000000000e+00,3.000000000000000000e+00"
    )

    loaded = backend.read(run_meta)
    assert_array_equal(loaded, data)
