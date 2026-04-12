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
"""Simulate command implementation."""

__all__ = []

from pathlib import Path

from flepimop2.meta import RunMeta
import numpy as np

from flepimop2._cli._cli_command import CliCommand
from flepimop2.configuration import ConfigurationModel
from flepimop2.parameter.abc import build as build_parameter
from flepimop2.scenario.abc import build as build_scenario
from flepimop2.simulator import Simulator


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

        Raises:
            ValueError: If the simulator is missing a simulation configuration.
        """
        config_model = ConfigurationModel.from_yaml(config)

        s0 = build_parameter(config_model.parameters["s0"])
        i0 = build_parameter(config_model.parameters["i0"])
        r0 = build_parameter(config_model.parameters["r0"])
        initial_state = np.array(
            [
                s0.sample().item(),
                i0.sample().item(),
                r0.sample().item(),
            ],
            dtype=np.float64,
        )
        params = {
            k: build_parameter(v).sample().item()
            for k, v in config_model.parameters.items()
            if k not in {"s0", "i0", "r0"}
        }

        simulator = Simulator.from_configuration_model(config_model, target=target)

        if simulator.simulate_config is None:
            msg = "simulate_config must be set before running the simulator."
            raise ValueError(msg)

        for component in ["system", "engine", "backend"]:
            name = getattr(simulator.simulate_config, component)
            config = getattr(simulator, f"{component}_config")
            self.info(f"  {component.capitalize()}: {name} => {config}")
        self.info(f"  Y0: {initial_state} [{type(initial_state)}]")
        self.info(f"  Params: {params} [{type(params)}]")
        self.info(f"  T: {simulator.simulate_config.times}")

        if dry_run:
            return

        if scenario_name := simulator.simulate_config.scenario:
            # extract scenario parameters from the configuration
            scenario_config = build_scenario(config_model.scenarios[scenario_name])
            counter = 0
            for scenario_tuple in scenario_config.scenarios():
                self.info(f"Running scenario: {scenario_tuple}")
                simulator.run(initial_state, (params | scenario_tuple._asdict()), meta = RunMeta(name = f"scenario_{counter}"))
                counter += 1
        else:
            simulator.run(initial_state, params)
