"""Simulate command implementation."""

__all__ = []

from pathlib import Path

from flepimop2._cli._cli_command import CliCommand
from flepimop2.configuration import ConfigurationModel
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

        simulator = Simulator.from_configuration_model(config_model, target=target)
        initial_state, params = simulator.resolve_inputs()

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

        simulator.run(initial_state, params)
