# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""A `SystemABC` which wraps a user-defined script file."""

from typing import Any

from flepimop2._utils._checked_partial import _checked_partial as _checked_partial
from flepimop2._utils._module import _as_dict, _load_module, _validate_function
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
    config = _as_dict(config)
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
