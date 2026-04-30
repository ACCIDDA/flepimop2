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

from typing import Self

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

    @classmethod
    def from_shorthand(cls, shorthand: str) -> Self:
        r"""
        Build a fixed parameter from shorthand argument text.

        Args:
            shorthand: The text inside the shorthand parentheses.

        Returns:
            A fixed parameter with the parsed numeric value.

        Raises:
            ValueError: If the shorthand cannot be parsed as a float.

        Examples:
            >>> from flepimop2.parameter.fixed import FixedParameter
            >>> FixedParameter.from_shorthand("3").value
            3.0
            >>> FixedParameter.from_shorthand("0.25").value
            0.25
            >>> FixedParameter.from_shorthand("-7").value
            -7.0
            >>> FixedParameter.from_shorthand('''
            ...   3.1415
            ... ''').value
            3.1415
            >>> try:
            ...     FixedParameter.from_shorthand("'x'")
            ... except ValueError as exc:
            ...     print(exc)
            FixedParameter shorthand must contain exactly one numeric value, got "'x'".
        """
        try:
            return cls(value=float(shorthand.strip()))
        except ValueError as exc:
            msg = (
                "FixedParameter shorthand must contain exactly one numeric value, "
                f"got {shorthand!r}."
            )
            raise ValueError(msg) from exc

    def sample(self) -> Float64NDArray:
        """
        Return the fixed value of the parameter.

        Returns:
            The fixed numeric value of the parameter.
        """
        return np.array([self.value], dtype=np.float64)
