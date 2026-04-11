"""Abstract base class for scenarios."""

__all__ = ["Float64NDArray", "ScenarioABC", "build"]

from abc import abstractmethod
from collections.abc import Iterable
from typing import Any, NamedTuple

from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel
from flepimop2.module import ModuleABC
from flepimop2.typing import Float64NDArray, IdentifierString


class ScenarioABC(ModuleABC):
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


def build(config: dict[IdentifierString, Any] | ModuleModel) -> ScenarioABC:
    """Build a `ScenarioABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance to construct the
            scenarios from.

    Returns:
        The constructed scenario instance.

    """
    return _build(config, "scenario", "flepimop2.scenario.grid", ScenarioABC)
