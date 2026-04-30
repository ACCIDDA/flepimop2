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
"""Grid scenario implementation."""

__all__ = ["Float64NDArray", "GridScenario"]

import itertools
from collections.abc import Iterable
from typing import Any, NamedTuple, cast

from flepimop2.configuration import ModuleModel
from flepimop2.scenario.abc import ScenarioABC
from flepimop2.typing import Float64NDArray, IdentifierString


class GridScenario(ModuleModel, ScenarioABC, module="grid"):
    """
    Grid scenario implementation.

    This scenario generates scenarios by taking the Cartesian product of parameter lists
    defined in the configuration.

    Attributes:
        module: The module type, fixed to "flepimop2.scenario.grid".
        parameters: A dictionary where keys are parameter names and values are lists of
            parameter values to be combined into scenarios.
    """

    parameters: dict[IdentifierString, list[Any]]

    @property
    def scenario_type(self) -> type[NamedTuple]:
        """
        Return the type of the scenario tuples for introspection purposes.

        Returns:
            The type of the scenario tuples.
        """
        return cast(
            "type[NamedTuple]",
            NamedTuple(
                "ScenarioTuple", [(k, type(v[0])) for k, v in self.parameters.items()]
            ),
        )

    def scenarios(self) -> Iterable[NamedTuple]:
        """
        Expose the scenarios.

        Yields:
            Scenario tuples from parameters.
        """
        param_lists = self.parameters.values()
        for p in itertools.product(*param_lists):
            yield self.scenario_type(*p)
