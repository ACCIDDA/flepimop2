"""Simulate command implementation."""

__all__ = []

from collections.abc import Iterable
from pathlib import Path

import numpy as np

from flepimop2._cli._cli_command import CliCommand
from flepimop2._parameters import ParameterCollection
from flepimop2._utils._click import _get_config_target
from flepimop2.backend.abc import build as build_backend
from flepimop2.configuration import ConfigurationModel
from flepimop2.engine.abc import build as build_engine
from flepimop2.meta import RunMeta
from flepimop2.system.abc import build as build_system


class SimulateCommand(CliCommand):
    """
    Run simulations based on a configuration file.

    This command runs epidemic simulations specified from a provided configuration file.
    The `CONFIG` argument should point to a valid configuration file.

    """

    def run(  # type: ignore[override]
        self,
        *,
        config: Path,
        groups: Iterable[str] | None,
        dry_run: bool,
        target: str | None = None,
    ) -> None:
        """
        Execute the simulation.

        Args:
            config: Path to the configuration file.
            groups: An iterable of parameter groups to apply.
            dry_run: Whether dry run mode is enabled.
            target: Optional target simulate config to use.

        """
        config_model = ConfigurationModel.from_yaml(config)
        simulate_config = _get_config_target(config_model.simulate, target, "simulate")

        system_config = config_model.systems[simulate_config.system].model_dump()
        engine_config = config_model.engines[simulate_config.engine].model_dump()
        backend_config = config_model.backends[simulate_config.backend].model_dump()

        parameter_collection = ParameterCollection(
            config_model.parameters,
            config_model.groups,
            groups,
        )
        params = parameter_collection.realize()
        initial_state = np.array(
            [params.pop("s0").item(), params.pop("i0").item(), params.pop("r0").item()],
            dtype=np.float64,
        )

        self.info(f"  System: {simulate_config.system} => {system_config}")
        self.info(f"  Engine: {simulate_config.engine} => {engine_config}")
        self.info(f"  Backend: {simulate_config.backend} => {backend_config}")
        self.info(f"  Y0: {initial_state} [{type(initial_state)}]")
        self.info(f"  Params: {params} [{type(params)}]")
        self.info(f"  T: {simulate_config.times}")

        if dry_run:
            return

        system = build_system(system_config)
        engine = build_engine(engine_config)
        backend = build_backend(backend_config)

        res = engine.run(system, simulate_config.t_eval, initial_state, params)
        backend.save(res, RunMeta())
