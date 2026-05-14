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
"""Abstract class for Engines to evolve Dynamic Systems."""

__all__ = ["EngineABC", "EngineProtocol", "build"]

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from pydantic import PrivateAttr

from flepimop2._utils._module import _build
from flepimop2.exceptions import ValidationIssue
from flepimop2.module import ModuleBase
from flepimop2.parameter.abc import ModelStateSpecification, ParameterValue
from flepimop2.system.abc import SystemABC
from flepimop2.typing import (
    Float64NDArray,
    IdentifierString,
    SystemProtocol,
)


@runtime_checkable
class EngineProtocol(Protocol):
    """Type-definition (Protocol) for engine runner functions."""

    def __call__(
        self,
        stepper: SystemProtocol,
        times: Float64NDArray,
        initial_state: dict[IdentifierString, ParameterValue],
        params: Mapping[IdentifierString, ParameterValue],
        model_state: ModelStateSpecification | None = None,
        **kwargs: Any,
    ) -> Float64NDArray:
        """Protocol for engine runner functions."""
        ...


def _no_run_func(
    stepper: SystemProtocol,
    times: Float64NDArray,
    initial_state: dict[IdentifierString, ParameterValue],
    params: Mapping[IdentifierString, ParameterValue],
    model_state: ModelStateSpecification | None = None,
    **kwargs: Any,
) -> Float64NDArray:
    msg = "EngineABC::_runner must be provided by a concrete implementation."
    raise NotImplementedError(msg)


class EngineABC(ModuleBase, module_namespace="engine"):
    """Abstract class for Engines to evolve Dynamic Systems."""

    _runner: Any = PrivateAttr(default=None)

    def model_post_init(self, __context: Any, /) -> None:  # noqa: ANN401
        """
        Set `_runner` to the no-op sentinel if not already overridden.

        Concrete subclasses should call `super().model_post_init(__context)`
        first, then assign `self._runner` to their runner function.

        Args:
            __context: Pydantic model post-init context.

        """
        super().model_post_init(__context)
        if self._runner is None:
            self._runner = _no_run_func

    def run(
        self,
        system: SystemABC,
        eval_times: Float64NDArray,
        initial_state: dict[IdentifierString, ParameterValue],
        params: Mapping[IdentifierString, ParameterValue],
        model_state: ModelStateSpecification | None = None,
        **kwargs: Any,
    ) -> Float64NDArray:
        """
        Run the engine with the provided system and parameters.

        Args:
            system: The dynamic system to be evolved.
            eval_times: Array of time points for evaluation.
            initial_state: Structured initial-state entries sampled from
                parameters.
            params: Additional parameters for the stepper.
            model_state: Specification describing the semantic ordering of the
                state entries.
            **kwargs: Additional keyword arguments for the engine.

        Returns:
            The evolved time x state array.
        """
        return self._runner(  # type: ignore[no-any-return]
            system.bind(),
            eval_times,
            initial_state,
            params,
            model_state=model_state,
            **kwargs,
        )

    def validate_system(  # noqa: PLR6301
        self,
        system: SystemABC,  # noqa: ARG002
    ) -> list[ValidationIssue] | None:
        """
        Validation hook for system properties.

        Args:
            system: The system to validate.

        Returns:
            A list of validation issues, or `None` if not implemented.
        """
        return None


def build(config: dict[str, Any] | ModuleBase | str) -> EngineABC:
    """Build a `EngineABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleBase` instance to construct the
            engine from. The configuration must define a `module`.

    Returns:
        The constructed engine instance.

    """
    return _build(config, "engine", EngineABC)
