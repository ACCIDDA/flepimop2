"""Abstract base class for flepimop2 processing steps."""

from abc import ABC, abstractmethod
from typing import Any

from flepimop2._utils._module import _load_builder, _resolve_module_name
from flepimop2.configuration import ModuleModel
from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue


class ProcessABC(ABC):
    """Abstract base class for flepimop2 processing steps."""

    def execute(self, *, dry_run: bool = False) -> None:
        """
        Execute a processing step.

        Args:
            dry_run: If True, the process will not actually execute but will simulate
                execution.

        Raises:
            Flepimop2ValidationError: If validation fails during a dry run.
        """
        if dry_run and (result := self._process_validate()) is not None:
            if result:
                raise Flepimop2ValidationError(result)
            return None
        return self._process(dry_run=dry_run)

    @abstractmethod
    def _process(self, *, dry_run: bool) -> None:
        """Backend-specific implementation for processing data."""
        ...

    def _process_validate(self) -> list[ValidationIssue] | None:  # noqa: PLR6301
        """
        Process validation hook.

        Returns:
            A boolean indicating if the process is valid, or `None` if not implemented.

        """
        return None


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
    module = _resolve_module_name(config_dict["module"], "process")
    config_dict["module"] = module
    builder = _load_builder(module)
    process = builder.build(config_dict)
    if not isinstance(process, ProcessABC):
        msg = "The built process is not an instance of ProcessABC."
        raise TypeError(msg)
    return process
