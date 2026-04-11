"""Grid scenario implementation."""

__all__ = ["Float64NDArray", "GridScenario"]

import itertools
from collections.abc import Iterable
from typing import Any, Literal, NamedTuple, cast

from flepimop2.configuration import ModuleModel
from flepimop2.scenario.abc import ScenarioABC
from flepimop2.typing import Float64NDArray, IdentifierString


class GridScenario(ModuleModel, ScenarioABC):
    """
    Grid scenario implementation.

    This scenario generates scenarios by taking the Cartesian product of parameter lists
    defined in the configuration.

    Attributes:
        module: The module type, fixed to "flepimop2.scenario.grid".
        parameters: A dictionary where keys are parameter names and values are lists of
            parameter values to be combined into scenarios.
    """

    module: Literal["flepimop2.scenario.grid"] = "flepimop2.scenario.grid"
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
        yield from itertools.product(*param_lists)
