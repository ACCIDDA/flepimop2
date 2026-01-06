from typing import Literal, Self

from pydantic import Field, model_validator

from flepimop2.configuration._module import ModuleGroupModel
from flepimop2.configuration._simulate import SimulateSpecificationModel
from flepimop2.configuration._types import IdentifierString
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
        groups: A dictionary mapping group names to parameter name mappings.
        simulate: A dictionary of simulation configurations.

    """

    name: str | None = None
    engines: ModuleGroupModel = Field(default_factory=dict)
    systems: ModuleGroupModel = Field(default_factory=dict)
    backends: ModuleGroupModel = Field(default_factory=dict)
    process: ModuleGroupModel = Field(default_factory=dict)
    parameters: ModuleGroupModel = Field(default_factory=dict)
    groups: dict[IdentifierString, dict[IdentifierString, IdentifierString]] = Field(
        default_factory=dict
    )
    simulate: dict[IdentifierString, SimulateSpecificationModel] = Field(
        default_factory=dict
    )

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
                f"{kind}s referenced in simulate not defined: "
                f"{missing}. Available {kind}s: {defined}"
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
              Value error, engines referenced in simulate not defined: {'fizz'}. Available engines: {'foo'} [...]
                For further information visit ...

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
              Value error, systems referenced in simulate not defined: {'buzz'}. Available systems: {'bar'} [...]
                For further information visit ...

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
              Value error, backends referenced in simulate not defined: {'db'}. Available backends: {'csv'} [...]
                For further information visit ...

        """  # noqa: E501
        self._check_simulate_engines_or_systems("backend")
        return self

    @model_validator(mode="after")
    def _check_groups_parameters(self) -> Self:
        """
        Ensure that all parameters referenced in groups exist.

        Returns:
            The validated `ConfigurationModel` instance.

        Raises:
            ValueError: If any of the parameters referenced in groups are not defined
                in parameters.

        Examples:
            >>> from flepimop2.configuration import ConfigurationModel
            >>> config = {
            ...     "parameters": {
            ...         "param1": {"module": "test"},
            ...     },
            ...     "groups": {
            ...         "group1": {
            ...             "new_param1": "missing_param",
            ...         },
            ...     },
            ... }
            >>> ConfigurationModel.model_validate(config)
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for ConfigurationModel
              Value error, parameters referenced in groups not defined: {'missing_param'}. Available parameters: {'param1'} [...]
                For further information visit ...

        """  # noqa: E501
        referenced_params = {
            param
            for group_mappings in self.groups.values()
            for param in group_mappings.values()
        }
        defined_params = set(self.parameters.keys())
        if missing := referenced_params - defined_params:
            msg = (
                f"parameters referenced in groups not defined: "
                f"{missing}. Available parameters: {defined_params}"
            )
            raise ValueError(msg)
        return self
