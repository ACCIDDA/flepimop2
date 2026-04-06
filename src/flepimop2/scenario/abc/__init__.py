"""Abstract base class for scenarios."""

__all__ = ["Float64NDArray", "ScenarioABC", "build"]

from abc import abstractmethod
from collections.abc import Iterable
from typing import Any

from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel
from flepimop2.module import ModuleABC
from flepimop2.typing import Float64NDArray


class ScenarioABC(ModuleABC):
    """Abstract base class for scenarios."""

    @abstractmethod
    def scenarios(self) -> Iterable[tuple]:
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
    return _build(config, "scenario", "flepimop2.scenario.grid", ScenarioABC)  # type: ignore[type-abstract]
