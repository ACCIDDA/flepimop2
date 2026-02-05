"""A `EngineABC` which wraps a user-defined script file."""

from pathlib import Path
from typing import Self

from pydantic import model_validator

from flepimop2._utils._module import _load_module, _validate_function
from flepimop2.configuration import ModuleModel
from flepimop2.engine.abc import EngineABC
from flepimop2.exceptions import ValidationIssue
from flepimop2.system.abc import SystemProperties
from flepimop2.typing import StateChangeEnum


class WrapperEngine(ModuleModel, EngineABC):
    """A `EngineABC` which wraps a user-defined script file."""

    script: Path
    state_change: StateChangeEnum = StateChangeEnum.FLOW

    @model_validator(mode="after")
    def _validate_script(self) -> Self:
        mod = _load_module(self.script, "flepimop2.engine.wrapped")
        if not _validate_function(mod, "runner"):
            msg = f"Module at {self.script} does not have a valid 'runner' function."
            raise AttributeError(msg)
        self._runner = mod.runner
        return self

    def validate_system_properties(
        self,
        properties: SystemProperties,
    ) -> list[ValidationIssue] | None:
        """
        Validate the compatibility of system properties with the engine.

        Args:
            properties: The system properties to validate.

        Returns:
            A list of validation issues, or `None` if not implemented.

        """
        if properties.state_change != self.state_change:
            return [
                ValidationIssue(
                    msg=(
                        f"Engine state change type, '{self.state_change}', is not "
                        "compatible with system state change type "
                        f"'{properties.state_change}'."
                    ),
                    kind="incompatible_system",
                )
            ]
        return None
