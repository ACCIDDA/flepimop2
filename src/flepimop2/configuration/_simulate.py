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
from pydantic import BaseModel, ConfigDict, Field

from flepimop2._utils._pydantic import RangeSpec, _to_np_array
from flepimop2.typing import Float64NDArray, IdentifierString


class SimulateSpecificationModel(BaseModel):
    """
    Model for specifying a simulation for flepimop2.

    Attributes:
        engine: The name of the engine to use for the simulation.
        system: The name of the system to simulate.
        backend: The name of the backend to use for the simulation.
        times: A list of time points at which to perform the simulation.
        params: Optional dictionary of parameters for the simulation.
        scenario: Optional name of the scenario to use for the simulation.
    """

    model_config = ConfigDict(extra="allow")

    engine: IdentifierString = "default"
    system: IdentifierString = "default"
    backend: IdentifierString = "default"
    times: RangeSpec
    params: dict[str, float] | None = Field(default_factory=dict)
    scenario: IdentifierString | None = None

    @property
    def t_eval(self) -> Float64NDArray:
        """
        Get the evaluation times as a NumPy array.

        Returns:
            A NumPy array of evaluation times.
        """
        return _to_np_array(self.times)
