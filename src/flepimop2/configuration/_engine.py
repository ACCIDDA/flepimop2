from pydantic import BaseModel, Field


class EngineModel(BaseModel):
    """Engine configuration model for flepimop2."""

    module: str = Field(min_length=1)
    options: dict[str, str] = Field(default_factory=dict)
