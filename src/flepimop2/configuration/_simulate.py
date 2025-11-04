from pydantic import BaseModel, ConfigDict, Field


class SimulateSpecificationModel(BaseModel):
    """
    Model for specifying a simulation for flepimop2.

    Attributes:
        engine: The name of the engine to use for the simulation.
        system: The name of the system to simulate.
        backend: The name of the backend to use for the simulation.
        times: A list of time points at which to perform the simulation.
        params: Optional dictionary of parameters for the simulation.
    """

    model_config = ConfigDict(extra="allow")

    engine: str = Field(min_length=1)
    system: str = Field(min_length=1)
    backend: str = Field(min_length=1)
    times: list[float] = Field(min_length=1)
    params: dict[str, float] | None = Field(default_factory=dict)
