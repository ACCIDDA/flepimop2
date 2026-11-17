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
"""Unit tests for the `BackendABC` save and read contract."""

import numpy as np

from flepimop2.axis import AxisCollection
from flepimop2.backend.abc import BackendABC
from flepimop2.meta import RunMeta
from flepimop2.parameter.abc import ModelStateSpecification
from flepimop2.typing import Array, Float64NDArray


def test_backend_save_forwards_context() -> None:
    """`save()` forwards data, run_meta, model_state, and axes to `_save()`."""
    received: dict[str, object] = {}

    class _ContextBackend(BackendABC, module="flepimop2.test.context_backend"):
        def _save(
            self,
            data: Array,
            run_meta: RunMeta,
            *,
            model_state: ModelStateSpecification | None = None,
            axes: AxisCollection | None = None,
        ) -> None:
            received["data"] = data
            received["run_meta"] = run_meta
            received["model_state"] = model_state
            received["axes"] = axes

        def _read(
            self,
            run_meta: RunMeta,
            *,
            model_state: ModelStateSpecification | None = None,
            axes: AxisCollection | None = None,
        ) -> Float64NDArray:
            del run_meta, model_state, axes
            return np.array([])

    backend = _ContextBackend()
    data = np.array([[1.0]])
    run_meta = RunMeta()
    model_state = ModelStateSpecification(parameter_names=("s0",))
    axes = AxisCollection()

    backend.save(data, run_meta, model_state=model_state, axes=axes)

    assert received["data"] is data
    assert received["run_meta"] is run_meta
    assert received["model_state"] is model_state
    assert received["axes"] is axes


def test_backend_save_forwards_none_defaults() -> None:
    """`save()` forwards None for model_state and axes when omitted."""
    received: dict[str, object] = {}

    class _ContextBackend(BackendABC, module="flepimop2.test.defaults_save_backend"):
        def _save(
            self,
            data: Array,
            run_meta: RunMeta,
            *,
            model_state: ModelStateSpecification | None = None,
            axes: AxisCollection | None = None,
        ) -> None:
            received["data"] = data
            received["run_meta"] = run_meta
            received["model_state"] = model_state
            received["axes"] = axes

        def _read(
            self,
            run_meta: RunMeta,
            *,
            model_state: ModelStateSpecification | None = None,
            axes: AxisCollection | None = None,
        ) -> Float64NDArray:
            del run_meta, model_state, axes
            return np.array([])

    backend = _ContextBackend()
    data = np.array([[2.0]])
    run_meta = RunMeta()

    backend.save(data, run_meta)

    assert received["data"] is data
    assert received["run_meta"] is run_meta
    assert received["model_state"] is None
    assert received["axes"] is None


def test_backend_read_forwards_context() -> None:
    """`read()` forwards run_meta, model_state, and axes to `_read()`."""
    received: dict[str, object] = {}

    class _ContextReadBackend(BackendABC, module="flepimop2.test.context_read"):
        def _save(
            self,
            data: Array,
            run_meta: RunMeta,
            *,
            model_state: ModelStateSpecification | None = None,
            axes: AxisCollection | None = None,
        ) -> None:
            del data, run_meta, model_state, axes

        def _read(
            self,
            run_meta: RunMeta,
            *,
            model_state: ModelStateSpecification | None = None,
            axes: AxisCollection | None = None,
        ) -> Float64NDArray:
            received["run_meta"] = run_meta
            received["model_state"] = model_state
            received["axes"] = axes
            return np.array([])

    backend = _ContextReadBackend()
    run_meta = RunMeta()
    model_state = ModelStateSpecification(parameter_names=("s0",))
    axes = AxisCollection()

    backend.read(run_meta, model_state=model_state, axes=axes)

    assert received["run_meta"] is run_meta
    assert received["model_state"] is model_state
    assert received["axes"] is axes


def test_backend_read_forwards_none_defaults() -> None:
    """`read()` forwards None for model_state and axes when omitted."""
    received: dict[str, object] = {}

    class _ContextReadBackend(
        BackendABC, module="flepimop2.test.defaults_read_backend"
    ):
        def _save(
            self,
            data: Array,
            run_meta: RunMeta,
            *,
            model_state: ModelStateSpecification | None = None,
            axes: AxisCollection | None = None,
        ) -> None:
            del data, run_meta, model_state, axes

        def _read(
            self,
            run_meta: RunMeta,
            *,
            model_state: ModelStateSpecification | None = None,
            axes: AxisCollection | None = None,
        ) -> Float64NDArray:
            received["run_meta"] = run_meta
            received["model_state"] = model_state
            received["axes"] = axes
            return np.array([])

    backend = _ContextReadBackend()
    run_meta = RunMeta()

    backend.read(run_meta)

    assert received["run_meta"] is run_meta
    assert received["model_state"] is None
    assert received["axes"] is None
