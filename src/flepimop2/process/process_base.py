"""Abstract base class for flepimop2 processing steps."""

from abc import ABC, abstractmethod
from typing import Any

from flepimop2._utils._module import _load_builder, _resolve_module_name
from flepimop2.configuration._module import ModuleModel


class ProcessABC(ABC):
    """Abstract base class for flepimop2 processing steps."""

    def execute(self, *, dry_run: bool = False) -> None:
        """
        Execute a processing step.

        Args:
            dry_run: If True, the process will not actually execute but will simulate
                execution.
        """
        return self._process(dry_run=dry_run)

    @abstractmethod
    def _process(self, *, dry_run: bool) -> None:
        """Backend-specific implementation for processing data."""
        ...


def build(config: dict[str, Any] | ModuleModel) -> ProcessABC:
    """Build a `ProcessABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary. The dict should contain a
            'module' key, which will be used to lookup the Process module path.
            The module will have "flepimop2.process." prepended.

    Returns:
        ProcessABC: The constructed process object.

    Raises:
        TypeError: If the built process is not an instance of ProcessABC.
    """
    config_dict = {"module": "flepimop2.process.shell"} | (
        config.model_dump() if isinstance(config, ModuleModel) else config
    )
    config_dict["module"] = _resolve_module_name(config_dict["module"], "process")
    builder = _load_builder(config_dict["module"])
    process = builder.build(config_dict)
    if not isinstance(process, ProcessABC):
        msg = "The built process is not an instance of ProcessABC."
        raise TypeError(msg)
    return process
