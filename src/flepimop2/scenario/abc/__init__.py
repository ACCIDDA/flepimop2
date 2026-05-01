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
"""Abstract base class for scenarios."""

__all__ = ["Float64NDArray", "ScenarioABC", "build"]

from abc import abstractmethod
from collections.abc import Iterable
from typing import Any, NamedTuple

from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel
from flepimop2.module import ModuleABC
from flepimop2.typing import Float64NDArray, IdentifierString


class ScenarioABC(ModuleABC, module_namespace="scenario"):
    """Abstract base class for scenarios."""

    @property
    @abstractmethod
    def scenario_type(self) -> type[NamedTuple]:
        """Return the type of the scenario tuples for introspection purposes.

        Returns:
            The type of the scenario tuples.
        """
        raise NotImplementedError

    @abstractmethod
    def scenarios(self) -> Iterable[NamedTuple]:
        """Expose the scenarios.

        Returns:
            An iterable of scenario tuples.
        """
        raise NotImplementedError


def build(config: dict[IdentifierString, Any] | ModuleModel | str) -> ScenarioABC:
    """Build a `ScenarioABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance to construct the
            scenarios from. The configuration must define a `module`.

    Returns:
        The constructed scenario instance.

    """
    return _build(config, "scenario", ScenarioABC)
