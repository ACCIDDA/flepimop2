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

from typing import Literal

import numpy as np

from flepimop2.axis import AxisCollection
from flepimop2.configuration import ModuleModel
from flepimop2.parameter.abc import ParameterABC, ParameterRequest, ParameterValue


class LinearParameter(ModuleModel, ParameterABC):
    """Parameter that scales one continuous axis by a configured slope."""

    module: Literal["flepimop2.parameter.linear"] = "flepimop2.parameter.linear"
    slope: float

    def sample(
        self,
        *,
        axes: AxisCollection | None = None,
        request: ParameterRequest | None = None,
    ) -> ParameterValue:
        """
        Sample values by multiplying one continuous axis's points by `slope`.

        Args:
            axes: Resolved runtime axes available for the current simulation.
            request: System request describing the required parameter shape.

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

        axis = axes[request.axes[0]]
        values = self.slope * np.asarray(axis.points(), dtype=np.float64)
        return ParameterValue(
            value=values,
            shape=axes.resolve_shape(request.axes),
        )
