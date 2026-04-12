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
"""Simulation orchestration for flepimop2."""

__all__ = ["Simulator"]
from flepimop2._utils._click import _get_config_target
from flepimop2.backend.abc import BackendABC
from flepimop2.backend.abc import build as build_backend
from flepimop2.configuration import (
    ConfigurationModel,
    ModuleModel,
    SimulateSpecificationModel,
)
from flepimop2.engine.abc import EngineABC
from flepimop2.engine.abc import build as build_engine
from flepimop2.exceptions import Flepimop2ValidationError
from flepimop2.meta import RunMeta
from flepimop2.system.abc import SystemABC
from flepimop2.system.abc import build as build_system
from flepimop2.typing import Float64NDArray


class Simulator:
    """
    Build and run a single simulation from configuration models.

    Attributes:
        system: The built system instance.
        engine: The built engine instance.
        backend: The built backend instance.
        target: Optional target simulate config to use.
        simulate_config: The resolved simulation specification.
        system_config: The resolved system configuration dict.
        engine_config: The resolved engine configuration dict.
        backend_config: The resolved backend configuration dict.

    """

    system: SystemABC
    engine: EngineABC
    backend: BackendABC
    target: str | None = None
    simulate_config: SimulateSpecificationModel | None = None
    system_config: ModuleModel | None = None
    engine_config: ModuleModel | None = None
    backend_config: ModuleModel | None = None

    def __init__(  # noqa: PLR0913
        self,
        system: SystemABC,
        engine: EngineABC,
        backend: BackendABC,
        *,
        target: str | None = None,
        simulate_config: SimulateSpecificationModel | None = None,
        system_config: ModuleModel | None = None,
        engine_config: ModuleModel | None = None,
        backend_config: ModuleModel | None = None,
    ) -> None:
        """
        Initialize the simulator with resolved components.

        Args:
            system: The built system instance.
            engine: The built engine instance.
            backend: The built backend instance.
            target: Optional target simulate config to use.
            simulate_config: The resolved simulation specification, if available.
            system_config: The resolved system configuration model, if available.
            engine_config: The resolved engine configuration model, if available.
            backend_config: The resolved backend configuration model, if available.

        Raises:
            Flepimop2ValidationError: If the engine is incompatible with the system.

        """
        self.target = target
        self.simulate_config = simulate_config
        self.system_config = system_config
        self.engine_config = engine_config
        self.backend_config = backend_config
        self.system = system
        self.engine = engine
        self.backend = backend

        if issues := self.engine.validate_system(self.system):
            raise Flepimop2ValidationError(issues)

    @classmethod
    def from_configuration_model(
        cls,
        config_model: ConfigurationModel,
        target: str | None = None,
    ) -> "Simulator":
        """
        Build a simulator from a configuration model.

        Returns:
            The constructed simulator instance.

        """
        simulate_config = _get_config_target(
            config_model.simulate,
            target,
            "simulate",
        )

        system_config = config_model.systems[simulate_config.system]
        engine_config = config_model.engines[simulate_config.engine]
        backend_config = config_model.backends[simulate_config.backend]

        system = build_system(system_config)
        engine = build_engine(engine_config)
        backend = build_backend(backend_config)

        return cls(
            system,
            engine,
            backend,
            target=target,
            simulate_config=simulate_config,
            system_config=system_config,
            engine_config=engine_config,
            backend_config=backend_config,
        )

    def run(
        self,
        initial_state: Float64NDArray,
        params: dict[str, float],
        meta: RunMeta = RunMeta(),
    ) -> Float64NDArray:
        """
        Run the simulation and persist results via the backend.

        Args:
            initial_state: The initial state array for the simulation.
            params: The parameter dict for the simulation.
            meta: Metadata about the simulation run.
        
        Returns:
            The simulation result array.

        Raises:
            ValueError: If `simulate_config` is not set.

        """
        if self.simulate_config is None:
            msg = "simulate_config must be set before running the simulator."
            raise ValueError(msg)
        res = self.engine.run(
            self.system,
            self.simulate_config.t_eval,
            initial_state,
            params,
        )
        self.backend.save(res, meta)
        return res
