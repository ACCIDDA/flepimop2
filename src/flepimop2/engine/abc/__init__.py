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

from typing import Any

from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel
from flepimop2.exceptions import ValidationIssue
from flepimop2.module import ModuleABC
from flepimop2.system.abc import SystemABC
from flepimop2.typing import (
    EngineProtocol,
    Float64NDArray,
    IdentifierString,
    SystemProtocol,
)


def _no_run_func(
    stepper: SystemProtocol,
    times: Float64NDArray,
    state: Float64NDArray,
    params: dict[IdentifierString, Any],
    **kwargs: Any,
) -> Float64NDArray:
    msg = "EngineABC::_runner must be provided by a concrete implementation."
    raise NotImplementedError(msg)


class EngineABC(ModuleABC, module_namespace="engine"):
    """Abstract class for Engines to evolve Dynamic Systems."""

    _runner: EngineProtocol

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        """
        Initialize the EngineABC.

        The default initialization sets the runner to a no-op function. Concrete
        implementations should override this with a valid runner function.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        self._runner = _no_run_func

    def run(
        self,
        system: SystemABC,
        eval_times: Float64NDArray,
        initial_state: Float64NDArray,
        params: dict[IdentifierString, Any],
        **kwargs: Any,
    ) -> Float64NDArray:
        """
        Run the engine with the provided system and parameters.

        Args:
            system: The dynamic system to be evolved.
            eval_times: Array of time points for evaluation.
            initial_state: The initial state array.
            params: Additional parameters for the stepper.
            **kwargs: Additional keyword arguments for the engine.

        Returns:
            The evolved time x state array.
        """
        return self._runner(
            system.bind(),
            eval_times,
            initial_state,
            params,
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


def build(config: dict[str, Any] | ModuleModel | str) -> EngineABC:
    """Build a `EngineABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance to construct the
            engine from. The configuration must define a `module`.

    Returns:
        The constructed engine instance.

    """
    return _build(config, "engine", EngineABC)
