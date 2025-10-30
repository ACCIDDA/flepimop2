"""Simulate command implementation."""

__all__ = []

from pathlib import Path

import numpy as np

import flepimop2.backend as backend_module
import flepimop2.engine as engine_module
import flepimop2.system as system_module
from flepimop2._cli._cli_command import CliCommand
from flepimop2.configuration import ConfigurationModel
from flepimop2.meta import RunMeta


class SimulateCommand(CliCommand):
    """
    Run simulations based on a configuration file.

    This command runs epidemic simulations specified from a provided configuration file.
    The `CONFIG` argument should point to a valid configuration file.
    """

    options = ("config", "verbosity", "dry_run")

    def run(self, *, config: Path, verbosity: int, dry_run: bool) -> None:  # type: ignore[override]
        """
        Execute the simulation.

        Args:
            config: Path to the configuration file.
            verbosity: Verbosity level (0-3).
            dry_run: Whether dry run mode is enabled.
        """
        configmodel = ConfigurationModel.from_yaml(config)
        simconfig = next(iter(configmodel.simulate.values()))

        backend = configmodel.backends[simconfig.backend].model_dump()
        stepper = configmodel.systems[simconfig.system].model_dump()
        engine = configmodel.engines[simconfig.engine].model_dump()
        params = configmodel.parameters

        times = np.asarray(simconfig.times, dtype=np.float64)
        initial_state = np.array(
            [
                params.pop("S0").value,
                params.pop("I0").value,
                params.pop("R0").value,
            ],
            dtype=np.float64,
        )
        pars = {k: v.value for k, v in params.items()}

        if dry_run:
            self.info(msg=f"Dry run, verbosity {verbosity}")
            self.info(f"Configuration {config} parsed successfully:")
            self.info(f"  System: {simconfig.system} => {stepper}")
            self.info(f"  Engine: {simconfig.engine} => {engine}")
            self.info(f"  Backend: {simconfig.backend} => {backend}")
            self.info(f"  Y0: {initial_state} [{type(initial_state)}]")
            self.info(f"  Params: {pars} [{type(pars)}]")
            self.info(f"  T: {times} [{type(times)}]")
            return

        stepobj = system_module.build(stepper)
        engineobj = engine_module.build(engine)
        backendobj = backend_module.build(backend)

        res = engineobj.run(stepobj, times, initial_state, pars)

        backendobj.save(res, RunMeta())
