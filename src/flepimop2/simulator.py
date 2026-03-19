"""Simulation orchestration for flepimop2."""

__all__ = ["Simulator"]

from flepimop2._utils._click import _get_config_target
from flepimop2.axis import AxisCollection
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
from flepimop2.parameter.abc import (
    ParameterRequest,
    ParameterValue,
)
from flepimop2.parameter.abc import build as build_parameter
from flepimop2.system.abc import SystemABC
from flepimop2.system.abc import build as build_system
from flepimop2.typing import Float64NDArray, IdentifierString


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
    parameter_configs: dict[IdentifierString, ModuleModel] | None = None
    axes: AxisCollection

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
        parameter_configs: dict[IdentifierString, ModuleModel] | None = None,
        axes: AxisCollection | None = None,
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
            parameter_configs: The resolved parameter configuration models, if
                available.
            axes: The resolved runtime axis collection for the simulation.

        Raises:
            Flepimop2ValidationError: If the engine is incompatible with the system.

        """
        self.target = target
        self.simulate_config = simulate_config
        self.system_config = system_config
        self.engine_config = engine_config
        self.backend_config = backend_config
        self.parameter_configs = parameter_configs
        self.axes = axes or AxisCollection()
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
            parameter_configs=config_model.parameters,
            axes=AxisCollection.from_config(config_model.axes),
        )

    def _sample_parameter(
        self,
        name: IdentifierString,
        request: ParameterRequest,
    ) -> ParameterValue:
        """
        Build and sample a requested parameter from configuration.

        Returns:
            The sampled parameter value and runtime shape metadata.

        Raises:
            KeyError: If the requested parameter is missing from configuration.
            ValueError: If parameter configuration has not been attached.
        """
        if self.parameter_configs is None:
            msg = "parameter_configs must be set before resolving parameters."
            raise ValueError(msg)
        if name not in self.parameter_configs:
            if request.optional:
                msg = f"Optional parameter '{name}' was requested but not configured."
                raise KeyError(msg)
            msg = f"Required parameter '{name}' was requested but not configured."
            raise KeyError(msg)
        parameter = build_parameter(self.parameter_configs[name])
        return parameter.sample(axes=self.axes, request=request)

    def resolve_inputs(
        self,
    ) -> tuple[
        dict[IdentifierString, ParameterValue],
        dict[IdentifierString, ParameterValue],
    ]:
        """
        Resolve configured parameters into an initial state and stepper inputs.

        Returns:
            Structured initial-state entries and structured stepper parameters.

        Raises:
            KeyError: If a required parameter is missing from configuration.
            ValueError: If model state cannot be resolved for the system.
        """
        state_spec = self.system.model_state(self.axes)
        if state_spec is None:
            msg = "System did not declare model_state."
            raise ValueError(msg)

        state_samples = {
            name: self._sample_parameter(name, request)
            for name, request in state_spec.requests().items()
        }
        resolved_params: dict[IdentifierString, ParameterValue] = {}
        for name, request in self.system.requested_parameters(self.axes).items():
            if self.parameter_configs is None or name not in self.parameter_configs:
                if request.optional:
                    continue
                msg = f"Required parameter '{name}' was requested but not configured."
                raise KeyError(msg)
            resolved_params[name] = self._sample_parameter(name, request)

        return state_samples, resolved_params

    def run(
        self,
        initial_state: dict[IdentifierString, ParameterValue] | None = None,
        params: dict[IdentifierString, ParameterValue] | None = None,
    ) -> Float64NDArray:
        """
        Run the simulation and persist results via the backend.

        Returns:
            The simulation result array.

        Raises:
            ValueError: If `simulate_config` is not set.

        """
        if self.simulate_config is None:
            msg = "simulate_config must be set before running the simulator."
            raise ValueError(msg)
        model_state = self.system.model_state(self.axes)
        if model_state is None:
            msg = "System did not declare model_state."
            raise ValueError(msg)
        if initial_state is None and params is None:
            initial_state, params = self.resolve_inputs()
        elif initial_state is None or params is None:
            msg = (
                "initial_state and params must either both be "
                "provided or both be omitted."
            )
            raise ValueError(msg)
        res = self.engine.run(
            self.system,
            self.simulate_config.t_eval,
            initial_state,
            params,
            model_state=model_state,
        )
        self.backend.save(res, RunMeta())
        return res
