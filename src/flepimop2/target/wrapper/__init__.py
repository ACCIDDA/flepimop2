"""A `TargetABC` which wraps a user-defined script file."""

__all__ = ["WrapperTarget"]

from pathlib import Path
from typing import Any, Literal, Self

from pydantic import model_validator

from flepimop2._utils._module import _load_module, _validate_function
from flepimop2.configuration import ModuleModel
from flepimop2.target.abc import TargetABC

class WrapperTarget(ModuleModel, TargetABC):
    """A `TargetABC` which wraps a user-defined script file."""

    module: Literal["flepimop2.target.wrapper"] = "flepimop2.target.wrapper"
    script: Path
    options: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_evaluator(self) -> Self:
        """
        Validator to load and validate the evaluator function from the script file.

        Returns:
            The validated `WrapperTarget` instance.

        Raises:
            AttributeError: If the module does not have a valid 'evaluator' function.
        """
        mod = _load_module(self.script, "flepimop2.target.wrapped")
        if not _validate_function(mod, "evaluator"):
            msg = f"Module at {self.script} does not have a valid 'evaluator' function."
            raise AttributeError(msg)
        self._evaluator = mod.evaluator
        return self
