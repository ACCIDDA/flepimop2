from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from flepimop2._utils._pydantic import _to_default_dict
from flepimop2.configuration._types import IdentifierString


class ModuleModel(BaseModel):
    """
    Module configuration model for flepimop2.

    Attributes:
        module: The type of the module.
    """

    model_config = ConfigDict(extra="allow")

    module: str = Field(min_length=1)


ModuleGroupModel = Annotated[
    dict[IdentifierString, ModuleModel], BeforeValidator(_to_default_dict)
]
"""Module group configuration model for flepimop2."""
