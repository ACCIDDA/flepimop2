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
from typing import Annotated, Any, TypeAlias

from pydantic import BeforeValidator

from flepimop2._utils._pydantic import _to_default_dict
from flepimop2.module import ModuleBase
from flepimop2.typing import IdentifierString

ModuleConfigurationValue: TypeAlias = ModuleBase | str
"""A module configuration value, either expanded config or shorthand text."""


ModuleGroupModel = Annotated[
    dict[IdentifierString, ModuleConfigurationValue], BeforeValidator(_to_default_dict)
]
"""Module group configuration model for flepimop2."""


def _coerce_parameter_configuration_value(value: Any) -> Any:  # noqa: ANN401
    """
    Rewrite bare numeric parameter config values to fixed-parameter shorthand.

    Args:
        value: The raw parameter configuration value.

    Returns:
        The original value, or a `fixed(...)` shorthand string for numeric inputs.

    Examples:
        >>> _coerce_parameter_configuration_value(0.3)
        'fixed(0.3)'
        >>> _coerce_parameter_configuration_value(2)
        'fixed(2)'
        >>> _coerce_parameter_configuration_value("fixed(0.3)")
        'fixed(0.3)'
        >>> _coerce_parameter_configuration_value("some-other-string")
        'some-other-string'
        >>> _coerce_parameter_configuration_value(True)
        True
        >>> _coerce_parameter_configuration_value(None) is None
        True
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"fixed({value!r})"
    return value


ParameterConfigurationValue: TypeAlias = Annotated[
    ModuleConfigurationValue,
    BeforeValidator(_coerce_parameter_configuration_value),
]
"""A parameter value, including bare numeric shorthand for fixed parameters."""


ParameterGroupModel = Annotated[
    dict[IdentifierString, ParameterConfigurationValue],
    BeforeValidator(_to_default_dict),
]
"""Parameter group configuration model for flepimop2."""
