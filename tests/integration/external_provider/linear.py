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
