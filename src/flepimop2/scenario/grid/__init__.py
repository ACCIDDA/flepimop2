"""Grid scenario implementation."""

__all__ = ["Float64NDArray", "GridScenario"]

import itertools
from typing import Literal

import numpy as np

from flepimop2.configuration import ModuleModel
from flepimop2.scenario.abc import ScenarioABC
from flepimop2.typing import Float64NDArray


class GridScenario(ModuleModel, ScenarioABC):
    """
    Grid scenario implementation.

    Examples:
        >>> from flepimop2.scenario.grid import GridScenario
        >>> scenario = GridScenario()
        >>> list(scenario.scenarios())
        []

    """

    module: Literal["flepimop2.scenario.grid"] = "flepimop2.scenario.grid"
    parameters: dict[IdentifierString, list[Any]]

    def scenarios(self):
        """
        Expose the scenarios.

        Yields:
            Scenario tuples from parameters.
        """
        param_lists = self.parameters.values()
        for combination in itertools.product(*param_lists):
            yield combination
