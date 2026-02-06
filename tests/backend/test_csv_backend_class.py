"""Unit tests for the `CsvBackend` class."""

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from flepimop2.backend.abc import build
from flepimop2.meta import RunMeta
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
