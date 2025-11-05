from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, BeforeValidator
from numpy.typing import NDArray
import numpy as np

from flepimop2.configuration._module import ModuleTarget
from flepimop2._utils._pydantic import _to_np_array


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

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    engine: ModuleTarget = "default"
    system: ModuleTarget = "default"
    backend: ModuleTarget = "default"
    times: Annotated[NDArray[np.float64], BeforeValidator(_to_np_array)]
    params: dict[str, float] | None = Field(default_factory=dict)
