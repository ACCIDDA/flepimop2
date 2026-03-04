"""Tests for `EngineABC` and default `WrapperEngine`."""

from typing import Any, cast

import numpy as np
import pytest

from flepimop2.configuration import IdentifierString
from flepimop2.engine.abc import EngineABC, EngineProtocol
from flepimop2.system.abc import SystemABC, SystemProtocol
from flepimop2.typing import Float64NDArray, StateChangeEnum


class DummySystem(SystemABC):
    """A dummy system for testing purposes."""

    module = "dummy"
    state_change = StateChangeEnum.FLOW


class DummyEngine(EngineABC):
    """A dummy engine for testing purposes."""

    module = "dummy"


def _class_runner(
    stepper: SystemProtocol,
    times: Float64NDArray,
    state: Float64NDArray,
    params: dict[IdentifierString, Any],
    **kwargs: Any,
) -> Float64NDArray:
    _ = kwargs
    return stepper(np.float64(times[0]), state, **params)


def _instance_runner(
    stepper: SystemProtocol,
    times: Float64NDArray,
    state: Float64NDArray,
    params: dict[IdentifierString, Any],
    **kwargs: Any,
) -> Float64NDArray:
    _ = kwargs
    return stepper(np.float64(times[0]), state, **params) + 1.0


def _built_runner(
    stepper: SystemProtocol,
    times: Float64NDArray,
    state: Float64NDArray,
    params: dict[IdentifierString, Any],
    **kwargs: Any,
) -> Float64NDArray:
    _ = kwargs
    return stepper(np.float64(times[0]), state, **params) + 2.0


class ClassRunnerEngine(EngineABC):
    """A simple engine with a class-level runner."""

    module = "class-runner"
    _runner = staticmethod(_class_runner)


class DynamicBuilderEngine(EngineABC):
    """An engine that dynamically constructs the runner via `build_runner`."""

    module = "dynamic-builder"

    def __init__(self) -> None:
        """Initialize call tracking for the dynamic build hook."""
        super().__init__()
        self.build_runner_calls = 0

    def build_runner(self) -> EngineProtocol:
        """
        Build and return a runner while counting hook invocations.

        Returns:
            The dynamically built runner function.
        """
        self.build_runner_calls += 1
        return _built_runner


class PresetInstanceRunnerEngine(EngineABC):
    """An engine that pre-sets `_runner` and should skip `build_runner`."""

    module = "preset-instance-runner"

    def __init__(self) -> None:
        """Initialize the engine with a pre-configured instance runner."""
        super().__init__()
        self._runner = _instance_runner

    def build_runner(self) -> EngineProtocol:
        """
        Fail if called; this class should use the preset instance runner.

        Raises:
            AssertionError: Always, because this hook should not be invoked.
        """
        msg = "build_runner should not be called when `_runner` is already set."
        raise AssertionError(msg)


def sample_step(
    time: np.float64, state: Float64NDArray, **kwargs: Any
) -> Float64NDArray:
    """
    A simple stepper function for testing purposes.

    Args:
        time: The current time as a float64.
        state: The current state as a numpy array.
        **kwargs: Additional keyword arguments, including 'offset'.

    Returns:
        The updated state after applying the stepper logic.
    """
    return (state + cast("float", kwargs["offset"])) * time


@pytest.mark.parametrize("engine", [DummyEngine()])
def test_abstraction_error(engine: EngineABC) -> None:
    """Test `EngineABC` raises `NotImplementedError` when not overridden."""
    system = DummySystem()
    system._stepper = sample_step
    with pytest.raises(NotImplementedError):
        engine.run(
            system,
            np.array([0.0], dtype=np.float64),
            np.array([1.0, 2.0, 3.0], dtype=np.float64),
            {},
        )


def test_class_level_runner_is_used() -> None:
    """Test class-level `_runner` is used when no dynamic builder is defined."""
    engine = ClassRunnerEngine()
    system = DummySystem()
    system._stepper = sample_step
    result = engine.run(
        system,
        np.array([2.0], dtype=np.float64),
        np.array([1.0, 2.0, 3.0], dtype=np.float64),
        {"offset": 1.0},
    )
    expected = np.array([4.0, 6.0, 8.0], dtype=np.float64)
    np.testing.assert_array_equal(result, expected)


def test_build_runner_hook_constructs_runner_once() -> None:
    """Test `build_runner` is called once and cached for subsequent runs."""
    engine = DynamicBuilderEngine()
    system = DummySystem()
    system._stepper = sample_step

    result_1 = engine.run(
        system,
        np.array([2.0], dtype=np.float64),
        np.array([1.0, 2.0, 3.0], dtype=np.float64),
        {"offset": 1.0},
    )
    result_2 = engine.run(
        system,
        np.array([1.0], dtype=np.float64),
        np.array([1.0, 2.0, 3.0], dtype=np.float64),
        {"offset": 2.0},
    )

    np.testing.assert_array_equal(
        result_1, np.array([6.0, 8.0, 10.0], dtype=np.float64)
    )
    np.testing.assert_array_equal(result_2, np.array([5.0, 6.0, 7.0], dtype=np.float64))
    assert engine.build_runner_calls == 1


def test_build_preserves_existing_instance_runner() -> None:
    """Test pre-set instance `_runner` takes precedence over `build_runner`."""
    engine = PresetInstanceRunnerEngine().build()
    system = DummySystem()
    system._stepper = sample_step
    result = engine.run(
        system,
        np.array([2.0], dtype=np.float64),
        np.array([1.0, 2.0, 3.0], dtype=np.float64),
        {"offset": 1.0},
    )
    expected = np.array([5.0, 7.0, 9.0], dtype=np.float64)
    np.testing.assert_array_equal(result, expected)
