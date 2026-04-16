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
"""Fixed parameter implementation."""

__all__ = ["FixedParameter"]

from typing import Any, Literal

import numpy as np

from flepimop2.axis import AxisCollection, ResolvedShape
from flepimop2.configuration import ModuleModel
from flepimop2.parameter.abc import ParameterABC, ParameterRequest, ParameterValue
from flepimop2.typing import IdentifierString


class FixedParameter(ModuleModel, ParameterABC):
    """
    Parameter with a fixed value.

    Examples:
        >>> from flepimop2.parameter.fixed import FixedParameter
        >>> param = FixedParameter(value=42.0)
        >>> param.sample().item()
        42.0

    """

    module: Literal["flepimop2.parameter.fixed"] = "flepimop2.parameter.fixed"
    value: float | int | list[Any]
    shape: tuple[IdentifierString, ...] = ()

    def sample(
        self,
        *,
        axes: AxisCollection | None = None,
        request: ParameterRequest | None = None,
    ) -> ParameterValue:
        """
        Return the fixed value of the parameter.

        Args:
            axes: Resolved runtime axes available for the current simulation.
            request: Optional system request describing the desired shape.

        Returns:
            The fixed parameter value with runtime shape metadata.

        Raises:
            ValueError: If the configured shape conflicts with the system request.
            ValueError: If a non-scalar fixed value has no named shape context.
            ValueError: If the configured value cannot satisfy the resolved shape.
        """
        axes = axes or AxisCollection()
        value = np.asarray(self.value, dtype=np.float64)

        configured_shape = axes.resolve_shape(self.shape) if self.shape else None
        requested_shape = (
            axes.resolve_shape(request.axes) if request is not None else None
        )

        if (
            configured_shape is not None
            and requested_shape is not None
            and configured_shape != requested_shape
        ):
            if request is None:
                msg = "request must be provided when validating a requested shape."
                raise ValueError(msg)
            msg = (
                f"FixedParameter shape {configured_shape.axis_names} does not match "
                f"requested shape {requested_shape.axis_names} for parameter "
                f"'{request.name}'."
            )
            raise ValueError(msg)

        target_shape = configured_shape or requested_shape
        if target_shape is None:
            if value.ndim > 0:
                msg = (
                    "Non-scalar FixedParameter values require either an explicit "
                    "'shape' configuration or a system request."
                )
                raise ValueError(msg)
            return ParameterValue(
                value=value,
                shape=ResolvedShape(),
            )

        if value.shape == target_shape.sizes:
            return ParameterValue(value=value, shape=target_shape)

        if value.ndim == 0 and (
            configured_shape is not None or (request is not None and request.broadcast)
        ):
            broadcast = np.broadcast_to(value, target_shape.sizes).astype(np.float64)
            return ParameterValue(value=broadcast, shape=target_shape)

        msg = (
            f"FixedParameter value shape {value.shape} is not compatible with "
            f"resolved shape {target_shape.sizes} for axes {target_shape.axis_names}."
        )
        raise ValueError(msg)
