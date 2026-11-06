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
from flepimop2.backend.abc import BackendABC, build
from flepimop2.backend.csv import CsvBackend
from flepimop2.meta import RunMeta
from flepimop2.parameter.abc import ModelStateSpecification
from flepimop2.typing import Float64NDArray


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


def test_csv_backend_writes_header_when_model_state_matches(tmp_path: Path) -> None:
    """A header row is written when model_state's columns match the data."""
    backend = CsvBackend(root=tmp_path)
    run_meta = RunMeta(name="header_test")
    data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    model_state = ModelStateSpecification(parameter_names=("s0", "i0", "r0"))

    backend.save(data, run_meta, model_state=model_state)

    file_path = backend._get_file_path(run_meta)
    first_line = file_path.read_text().splitlines()[0]
    assert first_line == "s0,i0,r0"

    loaded = backend.read(run_meta)
    assert_array_equal(loaded, data)


def test_csv_backend_expands_axes_in_header(tmp_path: Path) -> None:
    """Column labels expand per-axis-position when model_state declares axes."""
    backend = CsvBackend(root=tmp_path)
    run_meta = RunMeta(name="axes_test")
    # 1 parameter x 2 "age" positions = 2 columns.
    data = np.array([[1.0, 2.0]])
    model_state = ModelStateSpecification(parameter_names=("s0",), axes=("age",))
    axes = AxisCollection.from_config({
        "age": {"kind": "categorical", "labels": ["young", "old"]},
    })

    backend.save(data, run_meta, model_state=model_state, axes=axes)

    file_path = backend._get_file_path(run_meta)
    first_line = file_path.read_text().splitlines()[0]
    assert first_line == "s0[0],s0[1]"


def test_csv_backend_skips_header_on_column_mismatch(tmp_path: Path) -> None:
    """No header is written when model_state's column count doesn't match data."""
    backend = CsvBackend(root=tmp_path)
    run_meta = RunMeta(name="mismatch_test")
    # 3 data columns (e.g. a leading time column) but model_state only
    # describes 2 state entries -- can't label this safely.
    data = np.array([[0.0, 1.0, 2.0], [1.0, 4.0, 5.0]])
    model_state = ModelStateSpecification(parameter_names=("s0", "i0"))

    backend.save(data, run_meta, model_state=model_state)

    file_path = backend._get_file_path(run_meta)
    first_line = file_path.read_text().splitlines()[0]
    # No header written: the first line parses as numeric data, not labels.
    assert_array_equal(
        np.asarray(first_line.split(","), dtype=np.float64), data[0]
    )

    loaded = backend.read(run_meta)
    assert_array_equal(loaded, data)


def test_backend_save_does_not_forward_context_to_unaware_backend() -> None:
    """A `_save` without model_state/axes params never receives them."""
    received: dict[str, object] = {}

    class _LegacyBackend(BackendABC, module="flepimop2.test.legacy_backend"):
        def _save(self, data: object, run_meta: RunMeta) -> None:  # noqa: ARG002
            received["called"] = True

        def _read(self, run_meta: RunMeta) -> Float64NDArray:  # noqa: ARG002
            return np.array([])

    backend = _LegacyBackend()
    model_state = ModelStateSpecification(parameter_names=("s0",))
    backend.save(np.array([[1.0]]), RunMeta(), model_state=model_state)

    assert received == {"called": True}
