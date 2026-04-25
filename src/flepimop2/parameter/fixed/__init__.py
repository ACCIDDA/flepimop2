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

import numpy as np

from flepimop2.configuration import ModuleModel
from flepimop2.parameter.abc import ParameterABC
from flepimop2.typing import Float64NDArray


class FixedParameter(ModuleModel, ParameterABC, module="fixed"):
    """
    Parameter with a fixed value.

    Examples:
        >>> from flepimop2.parameter.fixed import FixedParameter
        >>> param = FixedParameter(value=42.0)
        >>> param.sample()
        array([42.])

    """

    value: float

    def sample(self) -> Float64NDArray:
        """
        Return the fixed value of the parameter.

        Returns:
            The fixed numeric value of the parameter.
        """
        return np.array([self.value], dtype=np.float64)
