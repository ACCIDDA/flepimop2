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
"""Cross-backend tests for the parameter-to-engine conversion seam."""

from collections.abc import Mapping
from typing import Any, ClassVar, cast

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from flepimop2._utils._array import array_backend
from flepimop2.axis import AxisCollection, ResolvedShape
from flepimop2.backend.abc import BackendABC
from flepimop2.configuration import SimulateSpecificationModel
from flepimop2.engine.abc import EngineABC
from flepimop2.meta import RunMeta
from flepimop2.parameter.abc import (
    ModelStateSpecification,
    ParameterABC,
    ParameterRequest,
    ParameterValue,
)
from flepimop2.parameter.fixed import FixedParameter
from flepimop2.simulator import Simulator
from flepimop2.system.abc import SystemProtocol, wrap
from flepimop2.typing import (
    Array,
    ArrayBackend,
    Float64NDArray,
    IdentifierString,
    StateChangeEnum,
)


class _JaxParameter(ParameterABC, module="test_array_backend_jax"):
    """Scalar JAX parameter used to exercise producer advertisement."""

    backend: ClassVar[ArrayBackend] = ArrayBackend.JAX
    value: float

    def sample(
        self,
        *,
        axes: AxisCollection | None = None,  # noqa: ARG002
        request: ParameterRequest | None = None,  # noqa: ARG002
    ) -> ParameterValue:
        """Produce one scalar JAX value.

        Returns:
            The scalar value and its empty named shape.
        """
        return ParameterValue(jnp.asarray(self.value), ResolvedShape())


def _step(
    time: np.float64,
    state: Float64NDArray,
    **params: ParameterValue,
) -> Float64NDArray:
    """Use only namespace-polymorphic arithmetic in the test system.

    Returns:
        The one-step state change in the state array's namespace.
    """
    state_value: Any = state
    rate_value: Any = params["rate"].value
    return cast("Float64NDArray", state_value + rate_value * time)


def _model_state(_axes: AxisCollection) -> ModelStateSpecification:
    """Declare the single evolving state value.

    Returns:
        The single-state model specification.
    """
    return ModelStateSpecification(parameter_names=("x",))


_SYSTEM = wrap(
    cast("SystemProtocol", _step),
    StateChangeEnum.FLOW,
    model_state=_model_state,
)


def _evolve(
    stepper: SystemProtocol,
    initial_state: dict[IdentifierString, ParameterValue],
    params: Mapping[IdentifierString, ParameterValue],
) -> Array:
    """Evolve one step while retaining the incoming namespace.

    Returns:
        The initial and evolved states in their original namespace.
    """
    x0 = initial_state["x"].value
    backend_stepper: Any = stepper
    x1 = backend_stepper(np.float64(1.0), x0, **params)
    xp: Any = x0.__array_namespace__()
    return cast("Array", xp.stack((x0, x1)))


def _numpy_runner(
    stepper: SystemProtocol,
    times: Float64NDArray,  # noqa: ARG001
    initial_state: dict[IdentifierString, ParameterValue],
    params: Mapping[IdentifierString, ParameterValue],
    model_state: ModelStateSpecification | None = None,  # noqa: ARG001
    **kwargs: Any,  # noqa: ARG001
) -> Float64NDArray:
    """Run the shared calculation using NumPy inputs.

    Returns:
        The initial and evolved NumPy states.
    """
    return cast("Float64NDArray", _evolve(stepper, initial_state, params))


def _jax_runner(
    stepper: SystemProtocol,
    times: Float64NDArray,  # noqa: ARG001
    initial_state: dict[IdentifierString, ParameterValue],
    params: Mapping[IdentifierString, ParameterValue],
    model_state: ModelStateSpecification | None = None,  # noqa: ARG001
    **kwargs: Any,  # noqa: ARG001
) -> Float64NDArray:
    """JIT the shared calculation to catch accidental host coercion.

    Returns:
        The initial and evolved JAX states.
    """
    shape = ResolvedShape()

    @jax.jit
    def solve(x0: Array, rate: Array) -> Array:
        return _evolve(
            stepper,
            {"x": ParameterValue(x0, shape)},
            {"rate": ParameterValue(rate, shape)},
        )

    return cast(
        "Float64NDArray",
        solve(initial_state["x"].value, params["rate"].value),
    )


class _NumpyEngine(EngineABC, module="test_array_backend_numpy"):
    """Engine requiring NumPy parameter payloads."""

    backend: ClassVar[ArrayBackend] = ArrayBackend.NUMPY

    def model_post_init(self, __context: Any, /) -> None:  # noqa: ANN401
        """Install the NumPy runner."""
        super().model_post_init(__context)
        self._runner = _numpy_runner


class _JaxEngine(EngineABC, module="test_array_backend_jax"):
    """Engine requiring JAX parameter payloads."""

    backend: ClassVar[ArrayBackend] = ArrayBackend.JAX

    def model_post_init(self, __context: Any, /) -> None:  # noqa: ANN401
        """Install the JAX runner."""
        super().model_post_init(__context)
        self._runner = _jax_runner


class _NoopBackend(BackendABC, module="test_array_backend_noop"):
    """Persistence sink for orchestration tests."""

    def _save(self, data: Float64NDArray, run_meta: RunMeta) -> None:
        """Accept the result without changing it."""

    def _read(self, run_meta: RunMeta) -> Float64NDArray:
        """Reading is outside this test's scope."""
        msg = "The no-op test backend does not store results."
        raise NotImplementedError(msg)


def _sample(backend: ArrayBackend, value: float) -> ParameterValue:
    """Sample the requested test producer.

    Returns:
        A scalar value from a producer advertising `backend`.
    """
    producer: ParameterABC
    if backend is ArrayBackend.NUMPY:
        producer = FixedParameter(value=value)
    else:
        producer = _JaxParameter(value=value)
    return producer.sample()


@pytest.mark.parametrize("producer_backend", [ArrayBackend.NUMPY, ArrayBackend.JAX])
@pytest.mark.parametrize(
    ("engine", "engine_backend"),
    [
        (_NumpyEngine(), ArrayBackend.NUMPY),
        (_JaxEngine(), ArrayBackend.JAX),
    ],
)
def test_simulator_converts_once_at_engine_boundary(
    producer_backend: ArrayBackend,
    engine: EngineABC,
    engine_backend: ArrayBackend,
) -> None:
    """Every NumPy/JAX producer-consumer pairing should run equivalently."""
    simulator = Simulator(
        _SYSTEM,
        engine,
        _NoopBackend(),
        simulate_config=SimulateSpecificationModel(times=[0.0, 1.0]),
    )

    result = simulator.run(
        initial_state={"x": _sample(producer_backend, 1.0)},
        params={"rate": _sample(producer_backend, 2.0)},
    )

    assert array_backend(cast("Array", result)) is engine_backend
    np.testing.assert_allclose(np.asarray(result), np.asarray([1.0, 3.0]))
