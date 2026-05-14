# Implementing Custom Engines and Systems

This guide shows how to implement `EngineABC` and `SystemABC` modules so they can be used in `flepimop2` for simulation. This guide mirrors the external provider guide, but focuses only on the engine/system interfaces.

Below is a minimal example creating new `EulerEngine` and `SirSystem`. You can copy these into your own module(s) under the `flepimop2.engine` and `flepimop2.system` namespaces.

## What are systems and engines?

To answer this question, let's start from a more general picture of doing modeling. There's are lots elements to that task, but they generally build upon the foundation of "having a model". We think about creating that foundation in three steps: defining __model worlds__, translating those worlds into __model representations__, and using those representations to create __model implementations__.

A __model world__ defines the interesting processes and states, and generally what is "in" the model (endogenous dynamics) versus "out" (exogenous effects). For the classic SIR model, the model world is roughly "There are Susceptible, Infectious, and Recovered populations. Those populations interact at a constant rate, and when S and I interact some constant fraction of interactions convert S to I. The I population converts at a constant rate into R population." Note that this world definition only concerns the states (S, I, R) and processes (infection of S into I; recovery of I into R), not any formal mathematics.

A __model representation__ translates the world into a particular mathematical framework. Taking again the classic SIR model, ordinary differential equations for the states would be a representation. As would Gillespie-style stochastic equations, update rules for individuals on a network, and so on.

A __model implementation__ creates a computationally-useful version of those representations.

The `flepimop2` tool captures these three steps using the configuration files, **System**s, and **Engine**s. This enables users to focus as much as possible in the __model world__ step, while developers automate as much as possible with modules for the other steps. Put another way: people should think of what they write in `flepimop2` configuration files as expressing their __model worlds__. Then, a **System** module translates that expression into __model representations__. Finally, an **Engine** module converts **System**s into fully-usable calculators. With reliable calculators in hand, researchers can then rapidly conduct their scientific or public health analyses.

To make all that work, `flepimop2` provides standard object definitions so that these parts can work together.

## Example System Implementation (`SirSystem`)

While any given **System** object represents a particular model world, a **System** *module* should be a way to build *many* model worlds. Thus, a module that only builds SIR is really only building one world: while that can be run with different parameters and different initial conditions and so on, there's really only one structure.

For now, however, we'll stick with a module that only contains this single world. Since there's only the single world, we can implement all the pieces directly:

```python
"""SIR system implementation."""

import numpy as np
from pydantic import PrivateAttr

from flepimop2.parameter.abc import ParameterValue
from flepimop2.system.abc import SystemABC, SystemProtocol
from flepimop2.typing import Float64NDArray, StateChangeEnum


def global_sir(
    time: np.float64,
    state: Float64NDArray,
    beta: ParameterValue,
    gamma: ParameterValue,
) -> Float64NDArray:
    """
    SIR model stepper function.

    Args:
        time: Current time point (unused in this autonomous system).
        state: Array of [S, I, R] populations.
        beta: Transmission rate.
        gamma: Recovery rate.

    Returns:
        Array of state derivatives [dS/dt, dI/dt, dR/dt].
    """
    return np.array([
        -beta.item() * state[0] * state[1],
        beta.item() * state[0] * state[1] - gamma.item() * state[1],
        gamma.item() * state[1]
    ])


class SirSystem(SystemABC, module="sir"):
    """SIR model system."""

    state_change: StateChangeEnum = StateChangeEnum.FLOW

    _stepper: SystemProtocol = PrivateAttr(default=None)

    def model_post_init(self, __context: object) -> None:
        super().model_post_init(__context)
        self.__pydantic_private__["_stepper"] = global_sir
```

Key elements in the system implementation:

- **SirSystem** inherits from **SystemABC**, which provides the Pydantic `BaseModel` foundation and all generic system capabilities automatically.
- `state_change` is a required field on every `SystemABC` subclass. Here it is given a fixed default since this system always uses the `FLOW` convention.
- `_stepper` is stored as a Pydantic `PrivateAttr` and wired up in `model_post_init`. Callables must be accessed and set through `self.__pydantic_private__["_stepper"]` rather than `self._stepper` to avoid Python's descriptor binding.
- The `module="sir"` class argument indicates how configuration files will indicate to use this module, i.e. `module: sir`.

## Engine Implementation (`EulerEngine`)

```python
"""Euler engine implementation."""

from typing import Any

import numpy as np
from pydantic import PrivateAttr

from flepimop2.engine.abc import EngineABC
from flepimop2.exceptions import ValidationIssue
from flepimop2.parameter.abc import ModelStateSpecification, ParameterValue
from flepimop2.system.abc import SystemABC, SystemProtocol
from flepimop2.typing import Float64NDArray, IdentifierString, StateChangeEnum


def runner(
    stepper: SystemProtocol,
    times: Float64NDArray,
    initial_state: dict[IdentifierString, ParameterValue],
    params: dict[IdentifierString, ParameterValue],
    model_state: ModelStateSpecification | None = None,
    **kwargs: Any,  # noqa: ARG001
) -> Float64NDArray:
    """
    Simple Euler runner for the SIR model.

    Args:
        stepper: The system stepper function.
        times: Array of time points.
        initial_state: Structured initial-state parameters.
        params: Additional structured parameters for the stepper.
        model_state: Specification describing how to order the initial state.
        **kwargs: Additional keyword arguments for the engine. Unused by this runner.

    Returns:
        The evolved time x state array.
    """
    # Implementors add their own logic here
    pass


class EulerEngine(EngineABC, module="euler"):
    """Euler integration engine."""

    _runner: Any = PrivateAttr(default=None)

    def model_post_init(self, __context: object) -> None:
        super().model_post_init(__context)
        self.__pydantic_private__["_runner"] = runner

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
```

Key elements in the engine implementation:

- `runner` drives the simulation by applying the stepper across time points.
- `EulerEngine` inherits `EngineABC` and stores its runner in `model_post_init` via `self.__pydantic_private__["_runner"]`. This pattern avoids descriptor binding that occurs when storing callables in `PrivateAttr` and accessing them via `self._runner`.
- The `module="euler"` class argument indicates how configuration files will indicate to use this module, i.e. `module: euler`.
- `EulerEngine` implements the optional `validate_system` hook to ensure that the system is compatible.
- No `build(...)` function is needed - `flepimop2` calls `EulerEngine.model_validate(config)` directly.

## Summary

Custom engines and systems are simple to implement once you know the required hooks. Keep the interfaces small and explicit, and let `flepimop2` handle construction and validation.

- Systems must inherit from `SystemABC` and supply a stepper (via `PrivateAttr` + `model_post_init`) as well as required attributes `module` and `state_change`.
- Engines must inherit from `EngineABC` and supply a runner function compatible with `SystemProtocol` (via `PrivateAttr` + `model_post_init`) as well as the required `module` attribute and the optional `validate_system` hook.
- Both use `model_post_init` for any initialization logic that runs after Pydantic has validated configuration fields.
- Neither requires a `build(...)` function - Pydantic's `model_validate` handles configuration-driven construction.
