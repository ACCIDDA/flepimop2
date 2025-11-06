"""Simulate command implementation."""

__all__ = []

from pathlib import Path

import numpy as np

import flepimop2.backend as backend_module
import flepimop2.engine as engine_module
import flepimop2.system as system_module
from flepimop2._cli._cli_command import CliCommand
from flepimop2._utils._click import _get_config_target
from flepimop2.configuration import ConfigurationModel
from flepimop2.meta import RunMeta


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
        dry_run: bool,
        target: str | None = None,
    ) -> None:
        """
        Execute the simulation.

        Args:
            config: Path to the configuration file.
            dry_run: Whether dry run mode is enabled.
            target: Optional target simulate config to use.
        """
        configmodel = ConfigurationModel.from_yaml(config)
        simconfig = _get_config_target(configmodel.simulate, target, "simulate")

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

        self.info(f"  System: {simconfig.system} => {stepper}")
        self.info(f"  Engine: {simconfig.engine} => {engine}")
        self.info(f"  Backend: {simconfig.backend} => {backend}")
        self.info(f"  Y0: {initial_state} [{type(initial_state)}]")
        self.info(f"  Params: {pars} [{type(pars)}]")
        self.info(f"  T: {times} [{type(times)}]")

        if dry_run:
            return

        stepobj = system_module.build(stepper)
        engineobj = engine_module.build(engine)
        backendobj = backend_module.build(backend)

        res = engineobj.run(stepobj, times, initial_state, pars)

        backendobj.save(res, RunMeta())
