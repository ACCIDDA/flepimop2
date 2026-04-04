"""A `SystemABC` which wraps a user-defined script file."""

from typing import Any

from flepimop2._utils._checked_partial import _checked_partial as _checked_partial
from flepimop2._utils._module import _load_module, _validate_function
from flepimop2.configuration import ModuleModel
from flepimop2.system.abc import SystemABC
from flepimop2.system.abc import wrap as system_wrap
from flepimop2.typing import (
    IdentifierString,
    StateChangeEnum,
    as_system_protocol,
)
from flepimop2.typing import (
    SystemProtocol as SystemProtocol,
)


def build(config: dict[IdentifierString, Any] | ModuleModel) -> SystemABC:
    """
    Build a `SystemABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance.

    Returns:
        The constructed system instance.

    Raises:
        AttributeError: If the loaded module does not have a valid 'stepper' function.
    """
    config = config if isinstance(config, dict) else config.model_dump()
    config_options = config.get("options", {})

    if script := config.get("script", config_options.get("script")):
        mod = _load_module(script, "flepimop2.system.wrapped")
        if not _validate_function(mod, "stepper"):
            msg = f"Module at {script} does not have a valid 'stepper' function."
            raise AttributeError(msg)

        stepper = as_system_protocol(mod.stepper)
        state_change: StateChangeEnum = StateChangeEnum(
            config.get("state_change", StateChangeEnum.ERROR)
        )
        config_options["script"] = script
        return system_wrap(
            stepper,
            state_change,
            config_options,
        )

    msg = (
        "Configuration must have a 'script' key either at the top level "
        "or within 'options'."
    )
    raise AttributeError(msg)
