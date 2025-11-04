from pydantic import BaseModel, ConfigDict, Field


class ModuleModel(BaseModel):
    """
    Module configuration model for flepimop2.

    Attributes:
        module: The type of the module.
    """

    model_config = ConfigDict(extra="allow")

    module: str = Field(min_length=1)
