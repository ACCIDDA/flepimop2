from typing import Literal, Self

from pydantic import Field, model_validator

from flepimop2.configuration._module import ModuleGroupModel
from flepimop2.configuration._parameters import ParameterSpecificationModel
from flepimop2.configuration._simulate import SimulateSpecificationModel
from flepimop2.configuration._yaml import YamlSerializableBaseModel


class ConfigurationModel(
    YamlSerializableBaseModel,
    alias_generator=lambda name: name.removesuffix("s"),
    validate_by_name=True,
):
    """
    Configuration model for flepimop2.

    This model serves as the parent container for a parsed configuration file.

    Attributes:
        name: An optional name for the configuration.
        engines: A dictionary of engine configurations.
        systems: A dictionary of system configurations.
        backends: A dictionary of backend configurations.
        process: A dictionary of process configurations.
        parameters: A dictionary of parameter configurations.
        simulate: A dictionary of simulation configurations.
    """

    name: str | None = None
    engines: ModuleGroupModel = Field(default_factory=dict)
    systems: ModuleGroupModel = Field(default_factory=dict)
    backends: ModuleGroupModel = Field(default_factory=dict)
    process: ModuleGroupModel = Field(default_factory=dict)
    parameters: dict[str, ParameterSpecificationModel] = Field(default_factory=dict)
    simulate: dict[str, SimulateSpecificationModel] = Field(default_factory=dict)

    def _check_simulate_engines_or_systems(
        self, kind: Literal["engine", "system", "backend"]
    ) -> None:
        """
        Ensure that all engines/systems/backends referenced in simulate exist.

        Args:
            kind: Either "engine", "system", or "backend" to specify which to check.

        Raises:
            ValueError: If any referenced engines or systems are not defined.
        """
        items = {getattr(sim, kind) for sim in self.simulate.values()}
        defined = set(getattr(self, f"{kind}s").keys())
        if missing := items - defined:
            msg = (
                f"{kind.capitalize()}s referenced in simulate not "
                f"defined: {missing}. Available {kind}s: {defined}"
            )
            raise ValueError(msg)

    @model_validator(mode="after")
    def _check_simulate_engines(self) -> Self:
        """
        Ensure that all engines referenced in simulate exist.

        Returns:
            The validated `ConfigurationModel` instance.

        Examples:
            >>> from flepimop2.configuration import ConfigurationModel
            >>> config = {
            ...     "engines": {
            ...         "foo": {"module": "test"},
            ...     },
            ...     "systems": {
            ...         "bar": {"module": "test"},
            ...     },
            ...     "backends": {
            ...         "csv": {"module": "test"},
            ...     },
            ...     "simulate": {
            ...         "sim1": {
            ...             "engine": "fizz",
            ...             "system": "bar",
            ...             "backend": "csv",
            ...             "times": [1.0, 2.0, 3.0],
            ...         },
            ...     },
            ... }
            >>> ConfigurationModel.model_validate(config)
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for ConfigurationModel
              Value error, Engines referenced in simulate not defined: {'fizz'}. Available engines: {'foo'} [...]
                For further information visit https://errors.pydantic.dev/2.12/v/value_error
        """  # noqa: E501
        self._check_simulate_engines_or_systems("engine")
        return self

    @model_validator(mode="after")
    def _check_simulate_systems(self) -> Self:
        """
        Ensure that all systems referenced in simulate exist.

        Returns:
            The validated `ConfigurationModel` instance.

        Examples:
            >>> from flepimop2.configuration import ConfigurationModel
            >>> config = {
            ...     "engines": {
            ...         "foo": {"module": "test"},
            ...     },
            ...     "systems": {
            ...         "bar": {"module": "test"},
            ...     },
            ...     "backends": {
            ...         "csv": {"module": "test"},
            ...     },
            ...     "simulate": {
            ...         "sim1": {
            ...             "engine": "foo",
            ...             "system": "buzz",
            ...             "backend": "csv",
            ...             "times": [1.0, 2.0, 3.0],
            ...         },
            ...     },
            ... }
            >>> ConfigurationModel.model_validate(config)
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for ConfigurationModel
              Value error, Systems referenced in simulate not defined: {'buzz'}. Available systems: {'bar'} [...]
                For further information visit https://errors.pydantic.dev/2.12/v/value_error
        """  # noqa: E501
        self._check_simulate_engines_or_systems("system")
        return self

    @model_validator(mode="after")
    def _check_simulate_backends(self) -> Self:
        """
        Ensure that all backends referenced in simulate exist.

        Returns:
            The validated `ConfigurationModel` instance.

        Examples:
            >>> from flepimop2.configuration import ConfigurationModel
            >>> config = {
            ...     "engines": {
            ...         "foo": {"module": "test"},
            ...     },
            ...     "systems": {
            ...         "bar": {"module": "test"},
            ...     },
            ...     "backends": {
            ...         "csv": {"module": "test"},
            ...     },
            ...     "simulate": {
            ...         "sim1": {
            ...             "engine": "foo",
            ...             "system": "bar",
            ...             "backend": "db",
            ...             "times": [1.0, 2.0, 3.0],
            ...         },
            ...     },
            ... }
            >>> configuration = ConfigurationModel.model_validate(config)
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for ConfigurationModel
              Value error, Backends referenced in simulate not defined: {'db'}. Available backends: {'csv'} [...]
                For further information visit https://errors.pydantic.dev/2.12/v/value_error
        """  # noqa: E501
        self._check_simulate_engines_or_systems("backend")
        return self
