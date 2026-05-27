# Implementing Custom Parameters

This guide shows how to implement `ParameterABC` modules so they can be used in `flepimop2` simulations. It mirrors the engines/systems guide but focuses on the parameter interface.

## What are parameters?

Parameters supply the numeric values that systems need to run their dynamics. A parameter implementation knows how to produce a `ParameterValue` - an array-API value together with its resolved named shape - from whatever source makes sense: a fixed scalar, a distribution sampler, a file on disk, a formula that derives from other parameters, and so on.

Parameters are resolved by the `Simulator` before each run. The `Simulator` calls `requested_parameters` to discover what the parameter needs, resolves those dependencies (recursively, with cycle detection), and then calls `sample` with the resolved values injected via the `params` argument.

## Minimal parameter implementation

Every concrete parameter must:

1. Inherit from `ParameterABC` and supply a `module=` class argument.
2. Implement `sample`, which receives optional runtime context and returns a `ParameterValue`.

```python
"""Constant-rate parameter implementation."""

import numpy as np

from flepimop2.axis import AxisCollection, ResolvedShape
from flepimop2.parameter.abc import ParameterABC, ParameterRequest, ParameterValue


class ConstantParameter(ParameterABC, module="constant"):
    """Parameter that always returns the same scalar value."""

    rate: float

    def sample(
        self,
        *,
        axes: AxisCollection | None = None,
        request: ParameterRequest | None = None,
        params: dict[str, ParameterValue] | None = None,
    ) -> ParameterValue:
        """
        Return the configured rate as a scalar ParameterValue.

        Args:
            axes: Resolved runtime axes (unused by this parameter).
            request: System request describing the desired shape (unused).
            params: Resolved dependency values (unused by this parameter).

        Returns:
            A scalar ParameterValue wrapping `rate`.
        """
        return ParameterValue(
            value=np.array(self.rate, dtype=np.float64),
            shape=ResolvedShape(),
        )
```

Key elements:

- `ConstantParameter` inherits from `ParameterABC`. `ParameterABC` inherits from `ModuleBase`, so `rate` is a validated pydantic field.
- `module="constant"` tells `flepimop2` that a configuration entry with `module: constant` should build this class.
- `sample` always ignores `axes`, `request`, and `params` here because a constant has no dependencies and no shape requirements. The `ParameterValue` wraps a zero-dimensional NumPy array with an empty `ResolvedShape`.

In configuration, this looks like:

```yaml
parameters:
  r0:
    module: constant
    rate: 1.2
```

## Responding to the system's shape request

Systems declare what shape they expect a parameter to have via `ParameterRequest`. The `axes` argument carries the full axis collection for the simulation, and `request.axes` lists the axis names the system wants the parameter aligned with.

A parameter that needs to produce values for a specific axis - say, an age-stratified rate - should read `request.axes` and resolve the target shape from the provided `AxisCollection`:

```python
"""Age-stratified rate parameter."""

import numpy as np

from flepimop2.axis import AxisCollection
from flepimop2.parameter.abc import ParameterABC, ParameterRequest, ParameterValue


class AgeRateParameter(ParameterABC, module="age_rate"):
    """Per-age-group rates loaded from configuration."""

    rates: list[float]

    def sample(
        self,
        *,
        axes: AxisCollection | None = None,
        request: ParameterRequest | None = None,
        params: dict[str, ParameterValue] | None = None,
    ) -> ParameterValue:
        """
        Return per-age rates aligned with the requested axis.

        Args:
            axes: Resolved runtime axes for the simulation.
            request: System request declaring the expected axis name.
            params: Resolved dependency values (unused by this parameter).

        Returns:
            A ParameterValue shaped to the requested axis.

        Raises:
            ValueError: If axes or request are not provided.
            ValueError: If the number of rates does not match the axis size.
        """
        if axes is None or request is None:
            msg = "AgeRateParameter requires axes and a request."
            raise ValueError(msg)

        resolved_shape = axes.resolve_shape(request.axes)
        values = np.array(self.rates, dtype=np.float64)

        if values.shape != resolved_shape.sizes:
            msg = (
                f"AgeRateParameter has {len(self.rates)} rate(s) but the "
                f"'{request.axes[0]}' axis has size {resolved_shape.sizes[0]}."
            )
            raise ValueError(msg)

        return ParameterValue(value=values, shape=resolved_shape)
```

In configuration, this looks like:

```yaml
axes:
  age:
    kind: categorical
    labels: ['0-17', '18-64', '65+']

parameters:
  gamma:
    module: age_rate
    rates: [0.08, 0.10, 0.14]
```

The system requests `gamma` with `axes=("age",)`, and `AgeRateParameter` validates
that the three configured rates align with the three age labels before returning
the shaped `ParameterValue`.

## Declaring dependencies on other parameters

A parameter can depend on other configured parameters by overriding `requested_parameters`. The `Simulator` resolves those dependencies first and injects the resulting `ParameterValue` objects into `sample` via `params`.

This is useful when one parameter is computed from another - for example, an effective transmission rate that is the product of a baseline rate and a seasonal multiplier:

```python
"""Seasonally-adjusted rate parameter."""

import numpy as np

from flepimop2.axis import AxisCollection, ResolvedShape
from flepimop2.parameter.abc import ParameterABC, ParameterRequest, ParameterValue
from flepimop2.typing import IdentifierString


class SeasonalParameter(ParameterABC, module="seasonal"):
    """Scales a configured base parameter by a seasonal multiplier.

    `base` and `multiplier` are names of other configured parameters.
    The Simulator resolves them before calling `sample`.
    """

    base: IdentifierString
    multiplier: IdentifierString

    def requested_parameters(
        self,
        axes: AxisCollection,  # noqa: ARG002
    ) -> dict[IdentifierString, ParameterRequest]:
        """
        Declare the base and multiplier parameters as dependencies.

        Args:
            axes: Resolved runtime axes (unused here, but available for
                shape-aware dependency declarations).

        Returns:
            Requests for the `base` and `multiplier` parameters.
        """
        return {
            self.base: ParameterRequest(name=self.base),
            self.multiplier: ParameterRequest(name=self.multiplier),
        }

    def sample(
        self,
        *,
        axes: AxisCollection | None = None,  # noqa: ARG002
        request: ParameterRequest | None = None,  # noqa: ARG002
        params: dict[str, ParameterValue] | None = None,
    ) -> ParameterValue:
        """
        Return base * multiplier as a scalar ParameterValue.

        Args:
            axes: Resolved runtime axes (unused by this parameter).
            request: System request describing the desired shape (unused).
            params: Resolved dependency values injected by the Simulator.

        Returns:
            A scalar ParameterValue equal to base * multiplier.

        Raises:
            ValueError: If params is None or missing a required key.
        """
        resolved = params or {}
        value = resolved[self.base].item() * resolved[self.multiplier].item()
        return ParameterValue(
            value=np.array(value, dtype=np.float64),
            shape=ResolvedShape(),
        )
```

With this implementation, the configuration looks like:

```yaml
parameters:
  beta_base: 0.3
  season_factor: 0.8
  beta_effective:
    module: seasonal
    base: beta_base
    multiplier: season_factor
```

The `Simulator` will resolve `beta_base` and `season_factor` first (they are `FixedParameter` scalars via shorthand), then call `SeasonalParameter.sample` with `params={"beta_base": ..., "season_factor": ...}`.

### Requesting shaped dependencies

A dependency can also carry a shape request. This is useful when the consuming parameter needs an axis-aligned array from its dependency rather than a scalar:

```python
def requested_parameters(
    self, axes: AxisCollection
) -> dict[IdentifierString, ParameterRequest]:
    return {
        "base_rates": ParameterRequest(
            name="base_rates",
            axes=("age",),
            broadcast=True,
        ),
    }
```

Setting `broadcast=True` tells the dependency that a scalar value is acceptable and should be broadcast to the requested axis size. Omitting it (or setting it to `False`) tells the dependency that the caller expects a fully-shaped array.

### Circular dependency detection

The `Simulator` walks the dependency graph depth-first and raises `ValueError` if a cycle is detected:

```
ValueError: Circular parameter dependency detected: beta_eff -> scale -> beta_eff.
```

This check runs at resolution time, before any `sample` calls are made.

## Configuration

Parameters are listed under the top-level `parameters` key. A bare scalar is automatically treated as a `FixedParameter`:

```yaml
parameters:
  gamma: 0.1  # shorthand: FixedParameter(value=0.1)
  beta:
    module: constant
    rate: 0.3
  beta_effective:
    module: seasonal
    base: beta
    multiplier: season_factor
  season_factor: 0.8
```

## Summary

- Parameters inherit from `ParameterABC` with a `module=` class argument.
- `sample(*, axes, request, params)` is the only required method. It must return a `ParameterValue` whose array shape matches `ResolvedShape`.
- Use `request.axes` together with `axes.resolve_shape(...)` to produce values aligned with what the system expects.
- Override `requested_parameters` to declare dependencies on other configured parameters. The `Simulator` injects resolved values via `params` before calling `sample`.
- Circular dependencies are detected automatically at resolution time.
- No `build(...)` function is needed - `flepimop2` calls `model_validate(config)` directly.
