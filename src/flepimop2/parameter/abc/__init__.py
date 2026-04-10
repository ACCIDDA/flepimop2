"""Abstract base class and runtime contracts for parameters."""

__all__ = [
    "ModelStateSpecification",
    "ParameterABC",
    "ParameterRequest",
    "ParameterValue",
    "build",
]

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np

from flepimop2._utils._module import _build
from flepimop2.axis import AxisCollection, ResolvedShape
from flepimop2.configuration import ModuleModel
from flepimop2.module import ModuleABC
from flepimop2.typing import Float64NDArray, IdentifierString


@dataclass(frozen=True, slots=True)
class ParameterRequest:
    """
    Request for a parameter value declared by a system.

    Attributes:
        name: Parameter name expected by the system.
        axes: Ordered named axes the resolved parameter should align with.
        broadcast: Whether a scalar parameter may be broadcast to the requested
            shape.
        optional: Whether the system can omit this parameter and rely on defaults.

    Notes:
        Systems typically create `ParameterRequest` objects in
        `SystemABC.requested_parameters()`. Parameter modules receive the request in
        `ParameterABC.sample()` and can use the shape metadata to decide how to
        materialize their values.

    Examples:
        >>> from pprint import pp
        >>> from flepimop2.parameter.abc import ParameterRequest
        >>> request = ParameterRequest(
        ...     name="gamma",
        ...     axes=("age",),
        ...     broadcast=True,
        ... )
        >>> pp(request)
        ParameterRequest(name='gamma', axes=('age',), broadcast=True, optional=False)
    """

    name: IdentifierString
    axes: tuple[IdentifierString, ...] = ()
    broadcast: bool = False
    optional: bool = False


@dataclass(frozen=True, slots=True)
class ModelStateSpecification:
    """
    Model State Specification.

    Describe how configured parameter entries assemble the evolving model state.

    Attributes:
        parameter_names: Ordered parameter names that define the model state.
        axes: Named axes shared by each state entry.
        broadcast: Whether scalar state entries may broadcast to the requested axes.
        labels: Optional human-readable labels such as compartment names.

    Notes:
        `ModelStateSpecification` defines the semantic order of model-state
        entries, but it does not prescribe how an engine should convert them
        into its internal representation. An ODE engine might use
        `np.stack(...)`, while another engine might preserve the dictionary
        form.

        Each state entry currently maps to exactly one configured parameter
        name. Reusing the same parameter name for multiple state entries is not
        supported because it would collapse when requests are materialized into
        a dictionary.

        For an age-by-region SEIR system with age labels
        `("age0_17", "age18_55", "age55_100")` and region labels
        `("Region A", "Region B")`, `parameter_names` could be
        `("S0", "E0", "I0", "R0")` and `axes` could be
        `("region", "age")`. An engine could then stack those entries into a
        `(4, 2, 3)` array ordered as `(compartment, region, age)`.

    Examples:
        >>> from flepimop2.parameter.abc import ModelStateSpecification
        >>> spec = ModelStateSpecification(
        ...     parameter_names=("s0", "i0", "r0"),
        ...     labels=("S", "I", "R"),
        ... )
        >>> tuple(spec.requests())
        ('s0', 'i0', 'r0')
    """

    parameter_names: tuple[IdentifierString, ...]
    axes: tuple[IdentifierString, ...] = ()
    broadcast: bool = False
    labels: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        """
        Validate any provided state labels align with parameter names.

        Raises:
            ValueError: If `labels` and `parameter_names` have different lengths.
            ValueError: If `parameter_names` contains duplicates.

        Examples:
            >>> from flepimop2.parameter.abc import ModelStateSpecification
            >>> spec = ModelStateSpecification(parameter_names=("s0",), labels=("S",))
            >>> spec.labels
            ('S',)
            >>> ModelStateSpecification(
            ...     parameter_names=("s0", "i0"),
            ...     labels=("S",),
            ... )
            Traceback (most recent call last):
                ...
            ValueError: ModelStateSpecification labels must match ...
            >>> ModelStateSpecification(
            ...     parameter_names=("s0", "s0"),
            ... )
            Traceback (most recent call last):
                ...
            ValueError: ModelStateSpecification parameter_names must be unique ...
        """
        if self.labels is not None and len(self.labels) != len(self.parameter_names):
            msg = (
                "ModelStateSpecification labels must match parameter_names length; "
                f"got {len(self.labels)} labels and {len(self.parameter_names)} "
                "parameter names."
            )
            raise ValueError(msg)
        if len(set(self.parameter_names)) != len(self.parameter_names):
            msg = (
                "ModelStateSpecification parameter_names must be unique so each "
                "state entry maps to exactly one configured parameter."
            )
            raise ValueError(msg)

    def requests(self) -> dict[IdentifierString, ParameterRequest]:
        """
        Convert this model-state specification into per-parameter requests.

        Returns:
            Sampling requests for each parameter used to initialize model state.
        """
        return {
            name: ParameterRequest(
                name=name,
                axes=self.axes,
                broadcast=self.broadcast,
            )
            for name in self.parameter_names
        }


@dataclass(frozen=True, slots=True)
class ParameterValue:
    """
    Sampled parameter value plus resolved runtime shape metadata.

    Attributes:
        value: The realized numeric value for this parameter.
        shape: Named runtime shape resolved against a concrete axis collection.

    Notes:
        `ParameterValue` intentionally keeps the payload small: it records the value
        itself and the resolved named shape. Richer provenance or caching metadata
        can be added later once those workflows are designed.

    Examples:
        >>> from pprint import pp
        >>> import numpy as np
        >>> from flepimop2.axis import ResolvedShape
        >>> from flepimop2.parameter.abc import ParameterValue
        >>> value = ParameterValue(
        ...     value=np.array([1.0, 2.0]),
        ...     shape=ResolvedShape(axis_names=("age",), sizes=(2,)),
        ... )
        >>> pp(value)
        ParameterValue(value=array([1., 2.]),
                       shape=ResolvedShape(axis_names=('age',), sizes=(2,)))
    """

    value: Float64NDArray
    shape: ResolvedShape

    def __post_init__(self) -> None:
        """
        Normalize to a float64 array and validate its resolved shape.

        Raises:
            ValueError: If the array shape does not match the resolved named shape.

        Examples:
            >>> import numpy as np
            >>> from flepimop2.axis import ResolvedShape
            >>> from flepimop2.parameter.abc import ParameterValue
            >>> ParameterValue(value=np.array(42.0), shape=ResolvedShape()).item()
            42.0
            >>> ParameterValue(
            ...     value=np.array([1.0, 2.0]),
            ...     shape=ResolvedShape(axis_names=("age",), sizes=(3,)),
            ... )
            Traceback (most recent call last):
                ...
            ValueError: ParameterValue shape mismatch: array has shape ...
        """
        value = np.asarray(self.value, dtype=np.float64)
        if value.shape != self.shape.sizes:
            msg = (
                "ParameterValue shape mismatch: array has shape "
                f"{value.shape}, but resolved shape is {self.shape.sizes} "
                f"for axes {self.shape.axis_names}."
            )
            raise ValueError(msg)
        object.__setattr__(self, "value", value)

    def item(self) -> float:
        """
        Return the scalar item from a scalar parameter value.

        Returns:
            The scalar value as a Python float.

        Examples:
            >>> import numpy as np
            >>> from flepimop2.axis import ResolvedShape
            >>> from flepimop2.parameter.abc import ParameterValue
            >>> ParameterValue(value=np.array(3.14), shape=ResolvedShape()).item()
            3.14
        """
        return float(self.value.item())


class ParameterABC(ModuleABC):
    """
    Abstract base class for parameter modules.

    Notes:
        Concrete parameter implementations should use `request` to decide how to
        materialize their output for a particular system. For example, a fixed scalar
        parameter may broadcast to a requested age axis, while a data-backed
        parameter may validate that its loaded data already matches the requested
        shape.
    """

    @abstractmethod
    def sample(
        self,
        *,
        axes: AxisCollection | None = None,
        request: ParameterRequest | None = None,
    ) -> ParameterValue:
        """
        Sample a value from the parameter.

        Args:
            axes: Resolved runtime axes available for this simulation.
            request: Optional system-declared request describing the expected shape
                and advisory type for the parameter.

        Returns:
            A sampled parameter value with resolved shape metadata.
        """
        raise NotImplementedError


def build(config: dict[str, Any] | ModuleModel) -> ParameterABC:
    """Build a `ParameterABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance to construct the
            parameter from.

    Returns:
        The constructed parameter instance.
    """
    return _build(config, "parameter", "flepimop2.parameter.wrapper", ParameterABC)
