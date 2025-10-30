"""Abstract base class for flepimop2 processing steps."""

from abc import ABC, abstractmethod
from typing import Any

from flepimop2._utils import _load_builder


class ProcessABC(ABC):
    """Abstract base class for flepimop2 processing steps."""

    def __init__(self) -> None:  # noqa: B027
        """
        Initialize the process with the given configuration.
        """
        pass

    def execute(self, *, dry_run: bool = False) -> None:
        """
        Execute a processing step.

        Args:
            dry_run: If True, the process will not actually execute but will simulate execution.
        """
        return self._process(dry_run=dry_run)

    @abstractmethod
    def _process(self, *, dry_run: bool) -> None:
        """Backend-specific implementation for processing data."""
        ...

def build(config: dict[str, Any]) -> ProcessABC:
    """Build a `ProcessABC` from a configuration dictionary.

    Args:
        config (dict[str, any]):
            Configuration dictionary. The dict should contain a
            'module' key, which will be used to lookup the Process module path.
            The module will have "flepimop2.process." prepended.

    Returns:
        ProcessABC: The constructed process object.
    """
    module = config.pop("module", "shell")
    module_abs = f"flepimop2.process.{module}"
    builder = _load_builder(module_abs)

    return builder.build(config)
