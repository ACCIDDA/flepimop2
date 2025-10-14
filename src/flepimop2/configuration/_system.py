from pydantic import BaseModel, ConfigDict, Field


class SystemModel(BaseModel):
    """Model configuration model for flepimop2."""

    model_config = ConfigDict(extra="allow")

    module: str = Field(min_length=1)
