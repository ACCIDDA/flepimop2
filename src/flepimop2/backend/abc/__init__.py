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
"""Abstract base class for flepimop2 file IO backends."""

__all__ = ["BackendABC", "build"]

import inspect
from abc import abstractmethod
from typing import Any

from flepimop2._utils._module import _build
from flepimop2.axis import AxisCollection
from flepimop2.meta import RunMeta
from flepimop2.module import ModuleBase
from flepimop2.parameter.abc import ModelStateSpecification
from flepimop2.typing import Array


def _accepts_kwarg(func: Any, name: str) -> bool:  # noqa: ANN401
    """
    Report whether a callable's signature would accept a given keyword argument.

    Used so `BackendABC.save()` can forward optional context (`model_state`,
    `axes`) only to `_save()` implementations that actually declare it,
    keeping older or third-party backends -- which only accept `(data,
    run_meta)` -- working unmodified.

    Args:
        func: The callable to inspect.
        name: The keyword argument name to check for.

    Returns:
        `True` if `func` declares a parameter named `name`, or accepts
        arbitrary keyword arguments, `False` otherwise.
    """
    parameters = inspect.signature(func).parameters
    if name in parameters:
        return True
    return any(p.kind is inspect.Parameter.VAR_KEYWORD for p in parameters.values())


class BackendABC(ModuleBase, module_namespace="backend"):
    """Abstract base class for flepimop2 file IO backends."""

    def save(
        self,
        data: Array,
        run_meta: RunMeta,
        *,
        model_state: ModelStateSpecification | None = None,
        axes: AxisCollection | None = None,
    ) -> None:
        """
        Save an array to storage.

        Args:
            data: The array to save.
            run_meta: Metadata about the current run.
            model_state: Optional specification describing the semantic
                ordering of `data`'s state entries (names, shared axes,
                human-readable labels). Forwarded to `_save()` only when the
                concrete backend's implementation declares it, so backends
                that write labelled output (e.g. a NetCDF variable name) can
                use it without requiring every backend to accept it.
            axes: Optional resolved runtime axes for the active simulation,
                giving sizes/labels for the axis names referenced by
                `model_state`. Forwarded under the same rule as `model_state`.
        """
        call_kwargs: dict[str, Any] = {}
        if model_state is not None and _accepts_kwarg(self._save, "model_state"):
            call_kwargs["model_state"] = model_state
        if axes is not None and _accepts_kwarg(self._save, "axes"):
            call_kwargs["axes"] = axes
        return self._save(data, run_meta, **call_kwargs)

    def read(self, run_meta: RunMeta) -> Array:
        """
        Read an array from storage.

        Args:
            run_meta: Metadata about the current run.

        Returns:
            The array read from storage.
        """
        return self._read(run_meta)

    @abstractmethod
    def _save(self, data: Array, run_meta: RunMeta) -> None:
        """Backend-specific implementation for saving data.

        Implementations that want the optional `model_state`/`axes` context
        `save()` can supply should widen this signature to accept them (e.g.
        `def _save(self, data, run_meta, **kwargs)`, or explicit `*,
        model_state=None, axes=None` keyword-only parameters); `save()`
        detects this via introspection and forwards accordingly.
        Implementations that don't need them keep this exact signature.
        """
        ...

    @abstractmethod
    def _read(self, run_meta: RunMeta) -> Array:
        """Backend-specific implementation for reading data."""
        ...


def build(config: dict[str, Any] | ModuleBase | str) -> BackendABC:
    """Build a `BackendABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary. The dict must contain a 'module' key, which
            will be used to lookup the backend module path. The module will have
            "flepimop2.backend." prepended.

    Returns:
        The constructed backend instance.

    """
    return _build(config, "backend", BackendABC)  # type: ignore[type-abstract]
