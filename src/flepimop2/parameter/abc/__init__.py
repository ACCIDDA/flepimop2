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
"""Abstract base class for parameters."""

__all__ = ["ParameterABC", "build"]

from abc import abstractmethod
from typing import Any

from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel
from flepimop2.module import ModuleABC
from flepimop2.typing import Float64NDArray


class ParameterABC(ModuleABC):
    """Abstract base class for parameters."""

    @abstractmethod
    def sample(self) -> Float64NDArray:
        """Sample a value from the parameter.

        Returns:
            A sampled value from the parameter.
        """
        raise NotImplementedError


def build(config: dict[str, Any] | ModuleModel) -> ParameterABC:
    """Build a `ParameterABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance to construct the
            parameter from.

    Returns:
        The constructed parameter instance.

    """
    return _build(config, "parameter", "flepimop2.parameter.wrapper", ParameterABC)
