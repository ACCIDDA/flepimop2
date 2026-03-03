# Implementing Custom Engines and Systems

This guide shows how to implement `EngineABC` and `SystemABC` so they can be loaded by `flepimop2` and used in simulations. It mirrors the style of the external provider guide, but focuses only on the engine/system interfaces.

For full API signatures and attributes, see the [`SystemABC` API reference](./../reference/api/system.md#flepimop2.system.abc.SystemABC) and the [`EngineABC` API reference](./../reference/api/engine.md#flepimop2.engine.abc.EngineABC).

Below is a minimal example creating new `EulerEngine` and `SirSystem`. You can copy these into your own module(s) under the `flepimop2.engine` and `flepimop2.system` namespaces.

## What are systems and engines?

- **System**: implements the model dynamics via a stepper and advertises its properties via the standardized required attributes or non-standardized options.
- **Engine**: runs a system stepper over time using an `EngineABC` runner.
- **Compatibility**: engines may validate system properties (e.g., flow vs. delta vs. state semantics) before running.

## System Implementation (`SirSystem`)

```python
"""Stepper function for SIR model integration tests."""

from typing import Any

import numpy as np

from flepimop2.configuration import ModuleModel
from flepimop2.system.abc import SystemABC
from flepimop2.typing import Float64NDArray, StateChangeEnum


def stepper(
    time: np.float64,  # noqa: ARG001
    state: Float64NDArray,
    **kwargs: Any,  # noqa: ARG001
) -> Float64NDArray:
    """
    ODE for an SIR model.

    Args:
        time: Current time (not used in this model).
        state: Current state array [S, I, R].
        **kwargs: Additional parameters (e.g. beta, gamma, etc.).

    Returns:
        The change in state.
    """
    # Implementors add their own logic here
    pass


class SirSystem(SystemABC):
    """SIR model system."""

    module = "flepimop2.system.sir"
    state_change = StateChangeEnum.FLOW

    def build_stepper(self):
        """
        Build the system stepper.

        Returns:
            The stepper function for this system.
        """
        return stepper


def build(config: dict[str, Any] | ModuleModel) -> SirSystem:  # noqa: ARG001
    """
    Build an SIR system.

    Returns:
        An instance of the SIR system.
    """
    return SirSystem()
```

Key elements in the system implementation:

- `stepper` defines the model dynamics which the engine will call repeatedly.
- `SirSystem` inherits `SystemABC`, defines the required attributes `module` and `state_change`, and overrides `build_stepper` to provide the stepper.
- `build(...)` provides a standard entry point so `flepimop2` can construct the system from configuration data. For more details on this you can read the [Creating An External Provider Package](./creating-an-external-provider-package.md) development guide.

For very simple systems, you can define a class-level `_stepper` instead of overriding `build_stepper`:

```python
class SirSystem(SystemABC):
    module = "flepimop2.system.sir"
    state_change = StateChangeEnum.FLOW
    _stepper = staticmethod(stepper)
```

## Engine Implementation (`EulerEngine`)

```python
"""Runner function for SIR model integration tests."""

from typing import Any

import numpy as np

from flepimop2.configuration import IdentifierString, ModuleModel
from flepimop2.engine.abc import EngineABC
from flepimop2.exceptions import ValidationIssue
from flepimop2.system.abc import SystemABC, SystemProtocol
from flepimop2.typing import Float64NDArray, StateChangeEnum


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
    # Implementors add their own logic here
    pass


class EulerEngine(EngineABC):
    """SIR model runner."""

    module = "flepimop2.engine.euler"

    def build_runner(self):
        """
        Build the engine runner.

        Returns:
            The runner function for this engine.
        """
        return runner

    def validate_system(self, system: SystemABC) -> list[ValidationIssue] | None:
        """
        Validation hook for system properties.

        Args:
            system: The system to validate.

        Returns:
            A list of validation issues, or `None` if not implemented.
        """
        if system.state_change != StateChangeEnum.FLOW:
            return [
                ValidationIssue(
                    msg=(
                        "Engine state change type, 'flow', is not "
                        "compatible with system state change type "
                        f"'{system.state_change}'."
                    ),
                    kind="incompatible_system",
                )
            ]
        return None


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
- `EulerEngine` inherits `EngineABC`, defines `module`, and overrides `build_runner` to provide the runner.
- `EulerEngine` implements the optional `validate_system` hook to ensure that the system is compatible.
- `build(...)` lets `flepimop2` construct the engine from configuration data.

For very simple engines, you can define a class-level `_runner` instead of overriding `build_runner`:

```python
class EulerEngine(EngineABC):
    module = "flepimop2.engine.euler"
    _runner = staticmethod(runner)
```

## Summary

Custom engines and systems are simple to implement once you know the required hooks. Keep the interfaces small and explicit, and let `flepimop2` handle construction and validation.

- Systems must supply a stepper function compatible with `SystemProtocol` as well as required attributes `module` and `state_change`.
- Engines must supply a runner function compatible with `EngineProtocol` as well as required attribute `module` and optional validation hook `validate_system`.
- `build(...)` provides the standard entry point for configuration-driven construction.
