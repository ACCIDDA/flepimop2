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
"""Unit tests for the `BackendABC` save-context forwarding."""

from typing import Any

import numpy as np

from flepimop2.axis import AxisCollection
from flepimop2.backend.abc import BackendABC
from flepimop2.meta import RunMeta
from flepimop2.parameter.abc import ModelStateSpecification
from flepimop2.typing import Float64NDArray


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
    axes = AxisCollection()
    backend.save(np.array([[1.0]]), RunMeta(), model_state=model_state, axes=axes)

    assert received == {"called": True}


def test_backend_save_forwards_context_to_explicit_params_backend() -> None:
    """A `_save` declaring model_state and axes receives them."""
    received: dict[str, object] = {}

    class _ContextBackend(BackendABC, module="flepimop2.test.context_backend"):
        def _save(
            self,
            data: object,  # noqa: ARG002
            run_meta: RunMeta,  # noqa: ARG002
            *,
            model_state: ModelStateSpecification | None = None,
            axes: AxisCollection | None = None,
        ) -> None:
            received["model_state"] = model_state
            received["axes"] = axes

        def _read(self, run_meta: RunMeta) -> Float64NDArray:  # noqa: ARG002
            return np.array([])

    backend = _ContextBackend()
    model_state = ModelStateSpecification(parameter_names=("s0",))
    axes = AxisCollection()
    backend.save(np.array([[1.0]]), RunMeta(), model_state=model_state, axes=axes)

    assert received["model_state"] is model_state
    assert received["axes"] is axes


def test_backend_save_forwards_context_to_var_keyword_backend() -> None:
    """A `_save` declaring `**kwargs` receives model_state and axes."""
    received: dict[str, object] = {}

    class _KwargsBackend(BackendABC, module="flepimop2.test.kwargs_backend"):
        def _save(
            self,
            data: object,  # noqa: ARG002
            run_meta: RunMeta,  # noqa: ARG002
            **kwargs: Any,
        ) -> None:
            received.update(kwargs)

        def _read(self, run_meta: RunMeta) -> Float64NDArray:  # noqa: ARG002
            return np.array([])

    backend = _KwargsBackend()
    model_state = ModelStateSpecification(parameter_names=("s0",))
    axes = AxisCollection()
    backend.save(np.array([[1.0]]), RunMeta(), model_state=model_state, axes=axes)

    assert received == {"model_state": model_state, "axes": axes}


def test_backend_save_filters_context_independently() -> None:
    """A `_save` accepting only one context argument does not receive the other."""
    received_state: dict[str, object] = {}
    received_axes: dict[str, object] = {}

    class _OnlyStateBackend(BackendABC, module="flepimop2.test.only_state_backend"):
        def _save(
            self,
            data: object,  # noqa: ARG002
            run_meta: RunMeta,  # noqa: ARG002
            *,
            model_state: ModelStateSpecification | None = None,
        ) -> None:
            received_state["model_state"] = model_state

        def _read(self, run_meta: RunMeta) -> Float64NDArray:  # noqa: ARG002
            return np.array([])

    class _OnlyAxesBackend(BackendABC, module="flepimop2.test.only_axes_backend"):
        def _save(
            self,
            data: object,  # noqa: ARG002
            run_meta: RunMeta,  # noqa: ARG002
            *,
            axes: AxisCollection | None = None,
        ) -> None:
            received_axes["axes"] = axes

        def _read(self, run_meta: RunMeta) -> Float64NDArray:  # noqa: ARG002
            return np.array([])

    model_state = ModelStateSpecification(parameter_names=("s0",))
    axes = AxisCollection()

    _OnlyStateBackend().save(
        np.array([[1.0]]), RunMeta(), model_state=model_state, axes=axes
    )
    assert received_state == {"model_state": model_state}

    _OnlyAxesBackend().save(
        np.array([[1.0]]), RunMeta(), model_state=model_state, axes=axes
    )
    assert received_axes == {"axes": axes}


def test_backend_save_does_not_forward_to_positional_only_backend() -> None:
    """A `_save` with positional-only params does not receive keyword context."""
    received: dict[str, object] = {}

    class _PositionalOnlyBackend(BackendABC, module="flepimop2.test.posonly_backend"):
        def _save(
            self,
            data: object,  # noqa: ARG002
            run_meta: RunMeta,  # noqa: ARG002
            axes: object = None,  # noqa: ARG002
            /,
        ) -> None:
            received["called"] = True

        def _read(self, run_meta: RunMeta) -> Float64NDArray:  # noqa: ARG002
            return np.array([])

    backend = _PositionalOnlyBackend()
    backend.save(
        np.array([[1.0]]),
        RunMeta(),
        model_state=ModelStateSpecification(parameter_names=("s0",)),
        axes=AxisCollection(),
    )
    assert received == {"called": True}
