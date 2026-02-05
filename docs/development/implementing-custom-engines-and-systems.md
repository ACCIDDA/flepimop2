# Implementing Custom Engines and Systems

This guide shows how to implement `EngineABC` and `SystemABC` so they can be loaded by `flepimop2` and used in simulations. It mirrors the style of the external provider guide, but focuses only on the engine/system interfaces.

Below is a minimal example creating new `EulerEngine` and `SirSystem`. You can copy these into your own module(s) under the `flepimop2.engine` and `flepimop2.system` namespaces.

## What are systems and engines?

- **System**: implements the model dynamics via a stepper and advertises its properties via `SystemABC.properties()`.
- **Engine**: runs a system stepper over time using an `EngineABC` runner.
- **Compatibility**: engines may validate system properties (e.g., flow vs. delta semantics) before running.

## System Implementation (`SirSystem`)

```python
"""Stepper function for SIR model integration tests."""

from typing import Any

import numpy as np

from flepimop2.configuration import ModuleModel
from flepimop2.system.abc import SystemABC, SystemProperties
from flepimop2.typing import Float64NDArray, StateChangeEnum


def stepper(
    time: np.float64,  # noqa: ARG001
    state: Float64NDArray,
    *,
    beta: float = 0.3,
    gamma: float = 0.1,
    **kwargs: Any,  # noqa: ARG001
) -> Float64NDArray:
    """
    ODE for an SIR model.

    Args:
        time: Current time (not used in this model).
        state: Current state array [S, I, R].
        beta: The infection rate.
        gamma: The recovery rate.
        **kwargs: Additional parameters (beta, gamma).

    Returns:
        The change in state.
    """
    y_s, y_i, _ = np.asarray(state, dtype=float)
    infection = beta * y_s * y_i / np.sum(state)
    recovery = gamma * y_i
    return np.array([-infection, infection - recovery, recovery], dtype=float)


class SirSystem(SystemABC):
    """SIR model system."""

    def __init__(self) -> None:
        """Initialize the SIR system with the SIR stepper."""
        self._stepper = stepper

    def properties(self) -> SystemProperties:
        """Return SIR system properties."""
        return SystemProperties(state_change=StateChangeEnum.FLOW)


def build(config: dict[str, Any] | ModuleModel) -> SirSystem:  # noqa: ARG001
    """
    Build an SIR system.

    Returns:
        An instance of the SIR system.
    """
    return SirSystem()
```

Key elements in the system implementation:

- `stepper` defines the model dynamics which the engine will call it repeatedly.
- `SirSystem` inherits `SystemABC` and assigns `_stepper` in `__init__`.
- `properties()` returns a `SystemProperties` object so engines can validate compatibility before running.
- `build(...)` provides a standard entry point so `flepimop2` can construct the system from configuration data. For more details on this you can read the [Creating An External Provider Package](./creating-an-external-provider-package.md) development guide.

## Engine Implementation (`EulerEngine`)

```python
"""Runner function for SIR model integration tests."""

from typing import Any

import numpy as np

from flepimop2.configuration import IdentifierString, ModuleModel
from flepimop2.engine.abc import EngineABC
from flepimop2.system.abc import SystemProtocol
from flepimop2.typing import Float64NDArray


def runner(
    stepper: SystemProtocol,
    times: Float64NDArray,
    state: Float64NDArray,
    params: dict[IdentifierString, Any],
    **kwargs: Any,  # noqa: ARG001
) -> Float64NDArray:
    """
    Simple Euler runner for the SIR model.

    Args:
        stepper: The system stepper function.
        times: Array of time points.
        state: The current state array.
        params: Additional parameters for the stepper.
        **kwargs: Additional keyword arguments for the engine. Unused by this runner.

    Returns:
        The evolved time x state array.
    """
    output = np.zeros((len(times), len(state)), dtype=float)
    output[0] = state
    for i, t in enumerate(times[1:]):
        if i == 0:
            continue
        dt = t - times[i - 1]
        dydt = stepper(times[i - 1], output[i - 1], **params)
        output[i] = output[i - 1] + (dydt * dt)
    return np.hstack((times.reshape(-1, 1), output))


class EulerEngine(EngineABC):
    """SIR model runner."""

    def __init__(self) -> None:
        """Initialize the SIR runner with the SIR runner function."""
        self._runner = runner


def build(config: dict[str, Any] | ModuleModel) -> EulerEngine:  # noqa: ARG001
    """
    Build an SIR engine.

    Returns:
        An instance of the SIR engine.
    """
    return EulerEngine()
```

Key elements in the engine implementation:

- `runner` drives the simulation by applying the stepper across time points.
- `EulerEngine` inherits `EngineABC` and assigns `_runner` in `__init__`.
- `build(...)` lets `flepimop2` construct the engine from configuration data.

## Summary

Custom engines and systems are simple to implement once you know the required hooks. Keep the interfaces small and explicit, and let `flepimop2` handle construction and validation.

- Systems must implement `properties()` and supply a stepper function.
- Engines must supply a runner function compatible with `SystemProtocol`.
- `build(...)` provides the standard entry point for configuration-driven construction.
