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
from typing import Annotated, Any, Literal, TypeAlias, cast

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from flepimop2._utils._pydantic import _to_default_dict
from flepimop2.module import ModuleABC
from flepimop2.typing import IdentifierString


class ModuleModel(BaseModel):
    """
    Module configuration model for flepimop2.

    Attributes:
        module: The module identifier for the configuration. Concrete subclasses
            may leave this as a general string field or specialize it to a fixed
            `Literal[...]` module path.
    """

    model_config = ConfigDict(extra="allow")

    module: str = Field(default="", min_length=1)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:  # noqa: PLW3201
        """
        Finalize the `module` field for `ModuleABC` subclasses after model creation.

        This keeps the explicit declaration API working while also allowing the
        shared `module="..."` class-definition shortcut implemented in `ModuleABC`.

        Args:
            **kwargs: Additional keyword arguments passed to parent classes.

        """
        super().__pydantic_init_subclass__(**kwargs)
        if not issubclass(cls, ModuleABC):
            return
        module = getattr(cls, "module", None)
        field = cls.model_fields.get("module")
        if not isinstance(module, str) or field is None:
            return
        field.annotation = cast("Any", Literal[module])
        field.default = module
        cls.model_rebuild(force=True)


ModuleConfigurationValue: TypeAlias = ModuleModel | str
"""A module configuration value, either expanded config or shorthand text."""


ModuleGroupModel = Annotated[
    dict[IdentifierString, ModuleConfigurationValue], BeforeValidator(_to_default_dict)
]
"""Module group configuration model for flepimop2."""
