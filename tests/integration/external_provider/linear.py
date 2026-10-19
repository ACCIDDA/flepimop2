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
"""Linear parameter implementation for external-provider integration tests."""

import numpy as np

from flepimop2.axis import AxisCollection
from flepimop2.parameter.abc import ParameterABC, ParameterRequest, ParameterValue
from flepimop2.typing import IdentifierString


class LinearParameter(ParameterABC, module="linear"):
    """Parameter computing ``slope * axis_points + intercept`` along one axis.

    ``slope`` and ``intercept`` may each be a bare float literal (the default)
    *or* the name of another configured parameter.  When a name is given,
    `requested_parameters` declares the dependency so the `Simulator` can
    resolve and inject the value before `sample` is called.
    """

    slope: float | IdentifierString
    intercept: float | IdentifierString = 0.0

    def requested_parameters(
        self,
        _axes: AxisCollection,
    ) -> dict[IdentifierString, ParameterRequest]:
        """Declare scalar parameter dependencies for slope and/or intercept.

        Returns:
            Parameter requests for any slope or intercept names that reference
            another configured parameter.
        """
        requests: dict[IdentifierString, ParameterRequest] = {}
        if isinstance(self.slope, str):
            requests[self.slope] = ParameterRequest(name=self.slope)
        if isinstance(self.intercept, str):
            requests[self.intercept] = ParameterRequest(name=self.intercept)
        return requests

    def sample(
        self,
        *,
        axes: AxisCollection | None = None,
        request: ParameterRequest | None = None,
        params: dict[IdentifierString, ParameterValue] | None = None,
    ) -> ParameterValue:
        """
        Sample values as ``slope * axis_points + intercept`` along one axis.

        ``slope`` and ``intercept`` are resolved from `params` when they were
        declared as parameter name dependencies, or taken as their literal
        float value otherwise.

        Args:
            axes: Resolved runtime axes available for the current simulation.
            request: System request describing the required parameter shape.
            params: Resolved dependency values injected by the `Simulator`.

        Returns:
            A `ParameterValue` aligned with the requested axis.

        Raises:
            ValueError: If runtime axes are unavailable.
            ValueError: If no request is provided.
            ValueError: If the request does not name exactly one axis.
        """
        if axes is None:
            msg = "LinearParameter requires runtime axes to sample values."
            raise ValueError(msg)
        if request is None:
            msg = "LinearParameter requires a parameter request to determine shape."
            raise ValueError(msg)
        if len(request.axes) != 1:
            msg = (
                "LinearParameter currently supports exactly one requested axis; "
                f"got {request.axes}."
            )
            raise ValueError(msg)

        resolved = params or {}
        slope = (
            resolved[self.slope].item() if isinstance(self.slope, str) else self.slope
        )
        intercept = (
            resolved[self.intercept].item()
            if isinstance(self.intercept, str)
            else self.intercept
        )

        axis = axes[request.axes[0]]
        values = slope * np.asarray(axis.points(), dtype=np.float64) + intercept
        return ParameterValue(
            value=values,
            shape=axes.resolve_shape(request.axes),
        )
