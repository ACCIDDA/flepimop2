"""A `EngineABC` which wraps a user-defined script file."""

from pathlib import Path
from typing import Self

from pydantic import model_validator

from flepimop2._utils._module import _load_module, _validate_function
from flepimop2.configuration import ModuleModel
from flepimop2.engine.abc import EngineABC


class WrapperEngine(ModuleModel, EngineABC):
    """A `EngineABC` which wraps a user-defined script file."""

    script: Path

    @model_validator(mode="after")
    def _validate_script(self) -> Self:
        mod = _load_module(self.script, "flepimop2.engine.wrapped")
        if not _validate_function(mod, "runner"):
            msg = f"Module at {self.script} does not have a valid 'runner' function."
            raise AttributeError(msg)
        self._runner = mod.runner
        return self
