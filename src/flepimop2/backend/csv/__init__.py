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

import csv
import itertools
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import Field, field_validator

from flepimop2.axis import AxisCollection
from flepimop2.backend.abc import BackendABC
from flepimop2.meta import RunMeta
from flepimop2.parameter.abc import ModelStateSpecification
from flepimop2.typing import Array, _TaggedArray


def _extract_axis_coords(
    axis_names: Sequence[str],
    axes: AxisCollection,
) -> tuple[tuple[str, ...], ...]:
    """
    Extract coordinate labels for each requested axis.

    Args:
        axis_names: Ordered axis names to extract coordinates for.
        axes: The axis collection containing axis definitions.

    Returns:
        A tuple of coordinate labels for each axis.

    Raises:
        ValueError: If an axis name is not found in the collection.
    """
    coords_per_axis: list[tuple[str, ...]] = []
    for name in axis_names:
        ax = axes.get(name)
        if ax is None:
            msg = f"Axis {name!r} not found in axes collection."
            raise ValueError(msg)
        if ax.labels:
            coords_per_axis.append(tuple(ax.labels))
        elif ax.kind == "continuous":
            coords_per_axis.append(tuple(str(p) for p in ax.points()))
        else:
            coords_per_axis.append(tuple(str(i) for i in range(ax.size)))
    return tuple(coords_per_axis)


def _build_axis_combos(
    axis_names: Sequence[str],
    axes: AxisCollection | None,
) -> list[tuple[str, ...]] | None:
    """
    Build cartesian product combinations of axis coordinates.

    Args:
        axis_names: The axis names to build combinations for.
        axes: The axis collection, or None.

    Returns:
        A list of coordinate tuples, or None if axes cannot be resolved.
    """
    if not axis_names:
        return [()]
    if axes is None:
        return None
    try:
        coords_per_axis = _extract_axis_coords(axis_names, axes)
    except ValueError:
        return None
    return list(itertools.product(*coords_per_axis))


def _write_long_csv(  # noqa: PLR0913
    file_path: Path,
    array: np.ndarray[Any, Any],
    state_names: Sequence[str],
    axis_names: Sequence[str],
    combos: Sequence[tuple[str, ...]],
    *,
    has_time_col: bool,
    is_1d_input: bool,
) -> None:
    """
    Write 2D state data to disk in tidy long format.

    Args:
        file_path: The target CSV path.
        array: 2D array of simulation results.
        state_names: Names of model state compartments.
        axis_names: Names of axes.
        combos: Cartesian product of axis coordinates.
        has_time_col: Whether column 0 contains explicit time values.
        is_1d_input: Whether input was originally a 1D array.
    """
    header = ["time", "state", *axis_names, "value"]
    with file_path.open("w", newline="", encoding="utf-8") as f:
        if is_1d_input:
            f.write("# ndim: 1\n")
        writer = csv.writer(f)
        writer.writerow(header)
        for t_idx in range(array.shape[0]):
            row = array[t_idx]
            t_val = row[0] if has_time_col else t_idx
            vals = row[1:] if has_time_col else row
            val_idx = 0
            for s_name in state_names:
                for combo in combos:
                    writer.writerow([t_val, s_name, *combo, vals[val_idx]])
                    val_idx += 1


def _build_predicates(
    model_state: ModelStateSpecification | None,
    axes: AxisCollection | None,
) -> dict[str, set[str]]:
    """
    Build row filtering predicates from model state and axes specifications.

    Args:
        model_state: Optional model state specification.
        axes: Optional resolved runtime axes.

    Returns:
        Mapping of column names to sets of allowed string values.
    """
    predicates: dict[str, set[str]] = {}
    if model_state is not None:
        allowed = set(model_state.parameter_names)
        if model_state.labels is not None:
            allowed.update(model_state.labels)
        predicates["state"] = allowed

    if axes is not None:
        for axis_name, axis in axes.items():
            if axis.labels is not None:
                predicates[str(axis_name)] = set(axis.labels)

    return predicates


def _filter_long_rows(
    header: Sequence[str],
    rows: Sequence[Sequence[str]],
    predicates: Mapping[str, set[str]],
) -> list[Sequence[str]]:
    """
    Filter long CSV rows against allowed column values.

    Args:
        header: The CSV column header names.
        rows: The raw CSV rows.
        predicates: Mapping of column names to allowed string values.

    Returns:
        The filtered sequence of CSV rows.
    """
    col_indices = {
        header.index(col): allowed
        for col, allowed in predicates.items()
        if col in header
    }
    if not col_indices:
        return list(rows)
    return [
        r
        for r in rows
        if all(r[idx] in allowed for idx, allowed in col_indices.items())
    ]


def _parse_long_tensor(
    dim_names: Sequence[str],
    rows: Sequence[Sequence[str]],
) -> tuple[np.ndarray[Any, Any], dict[str, tuple[str, ...]]]:
    """
    Reconstruct an ND tensor from long-format rows.

    Args:
        dim_names: The sequence of dimension names.
        rows: The long-format CSV data rows.

    Returns:
        A tuple of (reconstructed_tensor, coordinate_mapping).
    """
    dim_coords: dict[str, list[str]] = {d: [] for d in dim_names}
    seen: dict[str, set[str]] = {d: set() for d in dim_names}
    for r in rows:
        for d, val in zip(dim_names, r[:-1], strict=False):
            if val not in seen[d]:
                seen[d].add(val)
                dim_coords[d].append(val)

    shape = tuple(len(dim_coords[d]) for d in dim_names)
    indices = {
        d: {val: idx for idx, val in enumerate(dim_coords[d])} for d in dim_names
    }

    tensor = np.zeros(shape, dtype=np.float64)
    for r in rows:
        idx = tuple(indices[d][r[i]] for i, d in enumerate(dim_names))
        tensor[idx] = float(r[-1])

    coords = {d: tuple(dim_coords[d]) for d in dim_names}
    return tensor, coords


class CsvBackend(BackendABC, module="csv"):
    """CSV backend for saving and reading simulation results."""

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

    def _save(
        self,
        data: Array,
        run_meta: RunMeta,
        *,
        model_state: ModelStateSpecification | None = None,
        axes: AxisCollection | None = None,
    ) -> None:
        """
        Save an array to a CSV file.

        When `model_state` is provided and aligns with `data`, writes a tidy
        long-format CSV with columns `["time", "state", *axes, "value"]`.
        Otherwise, writes a raw numeric 2D CSV array.

        Args:
            data: The array to save.
            run_meta: Metadata about the current run.
            model_state: Optional specification describing state names and axes.
            axes: Optional resolved runtime axes.
        """
        file_path = self._get_file_path(run_meta)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        raw_array = np.asarray(data)

        if model_state is None:
            np.savetxt(file_path, raw_array, delimiter=",")
            return

        state_names = tuple(model_state.labels or model_state.parameter_names)
        axis_names: tuple[str, ...] = (
            tuple(model_state.axes) if model_state.axes else ()
        )
        combos = _build_axis_combos(axis_names, axes)
        if combos is None:
            np.savetxt(file_path, raw_array, delimiter=",")
            return

        expected_cols = len(state_names) * len(combos)
        is_1d = raw_array.ndim == 1
        arr = (
            raw_array.reshape(-1, 1)
            if (is_1d and len(state_names) == 1 and not axis_names)
            else (raw_array.reshape(1, -1) if is_1d else raw_array)
        )
        if arr.ndim != 2:
            np.savetxt(file_path, raw_array, delimiter=",")
            return

        has_time = arr.shape[1] == expected_cols + 1
        if not has_time and arr.shape[1] != expected_cols:
            np.savetxt(file_path, raw_array, delimiter=",")
            return

        _write_long_csv(
            file_path,
            arr,
            state_names,
            axis_names,
            combos,
            has_time_col=has_time,
            is_1d_input=is_1d,
        )

    def _read(
        self,
        run_meta: RunMeta,
        *,
        model_state: ModelStateSpecification | None = None,
        axes: AxisCollection | None = None,
    ) -> Array:
        """
        Read an array from a CSV file.

        If the file was saved in long format, parses the dimensions and
        returns an internal `_TaggedArray` annotated with `.dims` and `.coords`.
        If `model_state` or `axes` is provided, only matching states and axis
        coordinates are included. If the file was saved as a raw numeric CSV,
        returns a NumPy ndarray.

        Args:
            run_meta: Metadata about the current run.
            model_state: Optional model state specification to filter states.
            axes: Optional resolved runtime axes to filter coordinates.

        Returns:
            The read (and optionally filtered) array.
        """
        file_path = self._get_file_path(run_meta)
        is_1d = False
        with file_path.open(encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line == "# ndim: 1":
                is_1d = True
                first_line = f.readline().strip()

        parts = [p.strip() for p in first_line.split(",")]
        is_long = (
            len(parts) >= 3
            and parts[0] == "time"
            and parts[1] == "state"
            and parts[-1] == "value"
        )
        if not is_long:
            return np.loadtxt(file_path, delimiter=",")

        with file_path.open(encoding="utf-8") as f:
            lines = [line for line in f if not line.startswith("#")]
            reader = csv.reader(lines)
            header = next(reader)
            rows: Sequence[Sequence[str]] = list(reader)

        dim_names = tuple(header[:-1])
        predicates = _build_predicates(model_state, axes)
        if predicates:
            rows = _filter_long_rows(header, rows, predicates)

        if not rows:
            return _TaggedArray(np.array([], dtype=np.float64), dims=dim_names)

        tensor, coords = _parse_long_tensor(dim_names, rows)
        if is_1d and len(tensor.shape) >= 2 and tensor.shape[1:] == (1,):
            return _TaggedArray(
                tensor.reshape(-1),
                dims=("time",),
                coords={"time": coords["time"]},
            )

        return _TaggedArray(tensor, dims=dim_names, coords=coords)
