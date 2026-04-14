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
"""Abstract class for Dynamic Systems."""

__all__ = [
    "Flepimop2ValidationError",
    "SystemABC",
    "SystemProtocol",
    "ValidationIssue",
    "build",
]

import inspect
import sys
from abc import abstractmethod
from typing import Any

import numpy as np

from flepimop2._utils._checked_partial import _checked_partial, _consolidate_args
from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel
from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue
from flepimop2.module import ModuleABC
from flepimop2.typing import (
    Float64NDArray,
    IdentifierString,
    StateChangeEnum,
    SystemProtocol,
)

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class SystemABC(ModuleABC, module_namespace="system"):
    """
    Abstract class for Dynamic Systems.

    Attributes:
        module: The fully-qualified module name for the system.
        state_change: The type of state change.
        options: Optional dictionary of additional options the system exposes for
            `flepimop2` to take advantage of.

    """

    state_change: StateChangeEnum

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Ensure concrete subclasses define a valid state change type.

        Args:
            **kwargs: Additional keyword arguments passed to parent classes.

        Raises:
            TypeError: If a concrete subclass does not define `state_change`.

        """
        super().__init_subclass__(**kwargs)
        if inspect.isabstract(cls):
            return
        annotations = inspect.get_annotations(cls)
        has_state_change = (
            "state_change" in cls.__dict__ or "state_change" in annotations
        )
        if not has_state_change:
            msg = (
                f"Concrete class '{cls.__name__}' must define 'state_change' as "
                "a class attribute or type annotation."
            )
            raise TypeError(msg)

    def bind(
        self,
        params: dict[IdentifierString, Any] | None = None,
        **kwargs: Any,
    ) -> SystemProtocol:
        """
        Create a particular SystemProtocol.

        `bind()` translates a generic model specification into a particular
        realization. This can include statically defining parameters, but can
        also be called with no arguments to simply get the most flexible
        SystemProtocol available.

        Args:
            params: A dictionary of parameters to statically define for the system.
            **kwargs: Additional parameters to statically define for the system.

        Returns:
            A stepper function for this system with static parameters defined.

        Raises:
            TypeError: If params contains "time" or "state" keys,
                or parameters not in the System definition,
                or if the parameter values are incompatible with System definition.
        """  # noqa: DOC502
        checked_pars = _consolidate_args(
            forbidden={"time", "state"}, params=params, **kwargs
        )
        return self._bind_impl(params=checked_pars)

    @abstractmethod
    def _bind_impl(
        self, params: dict[IdentifierString, Any] | None = None
    ) -> SystemProtocol:
        """
        Abstract method to create a particular SystemProtocol.

        Concrete implementations of SystemABC must implement this method to
        define how to create a SystemProtocol with static parameters.

        Args:
            params: A dictionary of parameters to statically define for the System.

        Returns:
            A SystemProtocol for this System with static parameters defined.

        Raises:
            TypeError: If params contains "time" or "state" keys,
                or parameters not in the System definition,
                or if the parameter values are incompatible with System definition.
        """
        msg = "Concrete implementations must implement _bind_impl."
        raise NotImplementedError(msg)

    def step(
        self, time: np.float64, state: Float64NDArray, **params: Any
    ) -> Float64NDArray:
        """
        Perform a single step of the system's dynamics.

        Details:
            This method is only intended to be used for troubleshooting. Calling
            this method simply routes to `bind()` and then invokes the resulting
            SystemProtocol with the provided arguments.

        Args:
            time: The current time.
            state: The current state array.
            **params: Additional parameters for the stepper.

        Returns:
            The next state array after one step.
        """
        return self.bind()(time, state, **params)


class _AdapterSystem(SystemABC, module="wrapper"):
    """A `SystemABC` which wraps a user-defined function."""

    state_change: StateChangeEnum
    stepper: SystemProtocol
    options: dict[IdentifierString, Any]

    def __init__(
        self,
        state_change: StateChangeEnum,
        stepper: SystemProtocol,
        options: dict[IdentifierString, Any] | None = None,
    ) -> None:
        """
        Initialize the AdapterSystem with a state change and a stepper.

        Args:
            state_change: The type of state change for the system.
            stepper: A user-defined function that implements the system's dynamics.
            options: Optional dictionary of additional information about the system.

        """
        self.state_change = state_change
        self.stepper = stepper
        self.options = options or {}

    @override
    def _bind_impl(
        self, params: dict[IdentifierString, Any] | None = None
    ) -> SystemProtocol:
        return _checked_partial(
            func=self.stepper,
            params=params,
        )


def build(config: dict[IdentifierString, Any] | ModuleModel) -> SystemABC:
    """
    Build a `SystemABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance.

    Returns:
        The constructed system instance.

    """
    return _build(
        config,
        "system",
        "flepimop2.system.wrapper",
        SystemABC,
    )


def wrap(
    stepper: SystemProtocol,
    state_change: StateChangeEnum,
    options: dict[IdentifierString, Any] | None = None,
) -> SystemABC:
    """
    Adapt a user-defined function into a `SystemABC`.

    Args:
        stepper: A user-defined function that implements the system's dynamics.
        state_change: The type of state change for the system.
        options: Optional dictionary of additional information about the system.

    Returns:
        A `SystemABC` instance that wraps the provided stepper function.

    Raises:
        TypeError: If the provided stepper function does not conform to the expected
            signature or if offered an erroneous state_change.
    """
    if not isinstance(state_change, StateChangeEnum):
        msg = (
            "state_change must be an instance of StateChangeEnum; "
            f"got {type(state_change)}."
        )
        raise TypeError(msg)
    if state_change == StateChangeEnum.ERROR:
        msg = "state_change cannot be StateChangeEnum.ERROR for a valid system."
        raise TypeError(msg)

    return _AdapterSystem(
        state_change=state_change,
        stepper=stepper,
        options=options,
    )
