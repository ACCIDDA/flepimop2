import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

from flepimop2._utils._pydantic import RangeSpec, _to_np_array
from flepimop2.configuration._types import IdentifierString


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

    engine: IdentifierString = "default"
    system: IdentifierString = "default"
    backend: IdentifierString = "default"
    times: RangeSpec
    params: dict[str, float] | None = Field(default_factory=dict)

    @property
    def t_eval(self) -> NDArray[np.float64]:
        """
        Get the evaluation times as a NumPy array.

        Returns:
            A NumPy array of evaluation times.
        """
        return _to_np_array(self.times)
