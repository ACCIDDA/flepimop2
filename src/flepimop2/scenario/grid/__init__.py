"""Grid scenario implementation."""

__all__ = ["Float64NDArray", "GridScenario"]

import itertools
from collections.abc import Iterable
from typing import Any, Literal

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

    def scenarios(self) -> Iterable[tuple[Any, ...]]:
        """
        Expose the scenarios.

        Yields:
            Scenario tuples from parameters.
        """
        param_lists = self.parameters.values()
        yield from itertools.product(*param_lists)
