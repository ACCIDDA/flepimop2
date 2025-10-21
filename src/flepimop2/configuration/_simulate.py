from pydantic import BaseModel, ConfigDict, Field


class SimulateSpecificationModel(BaseModel):
    """Model for specifying a simulation for flepimop2."""

    model_config = ConfigDict(extra="allow")

    engine: str = Field(min_length=1)
    system: str = Field(min_length=1)
    backend: str = Field(min_length=1)
