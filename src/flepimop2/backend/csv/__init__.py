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
"""CSV backend for flepimop2."""

__all__ = ["CsvBackend"]

import itertools
import os
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import Field, field_validator

from flepimop2.axis import AxisCollection
from flepimop2.backend.abc import BackendABC
from flepimop2.meta import RunMeta
from flepimop2.parameter.abc import ModelStateSpecification
from flepimop2.typing import Array, Float64NDArray


def _column_labels(
    model_state: ModelStateSpecification,
    axes: AxisCollection | None,
) -> list[str] | None:
    """
    Expand a model-state specification into one label per data column.

    Each parameter name in `model_state.parameter_names` contributes one
    column when `model_state.axes` is empty, or one column per combination
    of its shared axes' positions otherwise (matching the row-major order an
    engine would use to flatten a stacked state array).

    Returns:
        One label per expected column, or `None` if `axes` is missing and
        `model_state.axes` is non-empty (sizes can't be resolved).
    """
    names = list(model_state.labels or model_state.parameter_names)
    if not model_state.axes:
        return names
    if axes is None:
        return None
    sizes = axes.sizes(*model_state.axes)
    combos = list(itertools.product(*(range(size) for size in sizes)))
    return [
        f"{name}[{','.join(str(c) for c in combo)}]"
        for name in names
        for combo in combos
    ]


class CsvBackend(BackendABC, module="csv"):
    """CSV backend for saving numpy arrays to CSV files."""

    root: Path = Field(default_factory=lambda: Path.cwd() / "model_output")

    @field_validator("root", mode="after")
    @classmethod
    def _validate_root(cls, root: Path) -> Path:
        """
        Validate that the root path is a writable directory.

        Args:
            root: The root path to validate.

        Returns:
            The validated root path.

        Raises:
            TypeError: If the root path is not a directory or is not writable.
        """
        if not (root.is_dir() and os.access(root, os.W_OK)):
            msg = f"The specified 'root' is not a directory or is not writable: {root}"
            raise TypeError(msg)
        return root

    def _get_file_path(self, run_meta: RunMeta) -> Path:
        """
        Generate a dynamic file path based on run metadata.

        Args:
            run_meta: Metadata about the current run.

        Returns:
            The dynamically generated file path.
        """
        timestamp_str = run_meta.timestamp.strftime("%Y%m%d_%H%M%S")
        name_part = f"{run_meta.name}_" if run_meta.name else ""
        filename = f"{name_part}{run_meta.action}_{timestamp_str}.csv"
        return self.root / filename

    def _save(self, data: Array, run_meta: RunMeta, **kwargs: Any) -> None:
        """
        Save an array to a CSV file.

        When a `model_state` keyword argument is supplied and its expanded
        column labels match `data`'s column count exactly, the labels are
        written as a plain (uncommented) header row. Otherwise the file is
        written without a header, as before -- a mismatch (e.g. an unrelated
        time column) is treated as "can't label this safely", not an error.

        Args:
            data: The array to save.
            run_meta: Metadata about the current run.
            **kwargs: Optional `model_state` (a `ModelStateSpecification`
                describing the semantic ordering of `data`'s columns) and
                `axes` (a resolved `AxisCollection` used to size any axes
                referenced by `model_state`), forwarded by `BackendABC.save()`.
        """
        file_path = self._get_file_path(run_meta)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        array = np.asarray(data)

        model_state: ModelStateSpecification | None = kwargs.get("model_state")
        axes: AxisCollection | None = kwargs.get("axes")
        header = ""
        labels = _column_labels(model_state, axes) if model_state is not None else None
        if labels is not None and array.ndim == 2 and len(labels) == array.shape[1]:
            header = ",".join(labels)

        np.savetxt(file_path, array, delimiter=",", header=header, comments="")

    def _read(self, run_meta: RunMeta) -> Float64NDArray:
        """
        Read a numpy array from a CSV file.

        Transparently skips a plain-text header row if one is present (the
        first line fails to parse as numeric data).

        Args:
            run_meta: Metadata about the current run.

        Returns:
            The numpy array read from the CSV file.
        """
        file_path = self._get_file_path(run_meta)
        with file_path.open() as fh:
            first_line = fh.readline()
        skiprows = 0
        try:
            np.asarray(first_line.strip().split(","), dtype=np.float64)
        except ValueError:
            skiprows = 1
        return np.loadtxt(file_path, delimiter=",", skiprows=skiprows)
