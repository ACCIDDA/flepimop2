"""Tests for `SystemABC` and default `WrapperSystem`."""

from typing import Any

import numpy as np
import pytest

from flepimop2.system.abc import SystemABC, SystemProtocol
from flepimop2.typing import Float64NDArray, StateChangeEnum


class DummySystem(SystemABC):
    """A dummy system for testing purposes."""

    module = "dummy"
    state_change = StateChangeEnum.FLOW


def _class_stepper(
    time: np.float64, state: Float64NDArray, **kwargs: Any
) -> Float64NDArray:
    offset = float(kwargs.get("offset", 0.0))
    return (state + offset) * time


def _instance_stepper(
    time: np.float64, state: Float64NDArray, **kwargs: Any
) -> Float64NDArray:
    _ = kwargs
    return state + time


def _built_stepper(
    time: np.float64, state: Float64NDArray, **kwargs: Any
) -> Float64NDArray:
    scale = float(kwargs.get("scale", 1.0))
    return state + (time * scale)


class ClassStepperSystem(SystemABC):
    """A simple system with a class-level stepper."""

    module = "class-stepper"
    state_change = StateChangeEnum.FLOW
    _stepper = staticmethod(_class_stepper)


class DynamicBuilderSystem(SystemABC):
    """A system that dynamically constructs the stepper via `build_stepper`."""

    module = "dynamic-builder"
    state_change = StateChangeEnum.FLOW

    def __init__(self) -> None:
        """Initialize call tracking for the dynamic build hook."""
        super().__init__()
        self.build_stepper_calls = 0

    def build_stepper(self) -> SystemProtocol:
        """
        Build and return a stepper while counting hook invocations.

        Returns:
            The dynamically built stepper function.
        """
        self.build_stepper_calls += 1
        return _built_stepper


class PresetInstanceStepperSystem(SystemABC):
    """A system that pre-sets `_stepper` and should skip `build_stepper`."""

    module = "preset-instance-stepper"
    state_change = StateChangeEnum.FLOW

    def __init__(self) -> None:
        """Initialize the system with a pre-configured instance stepper."""
        super().__init__()
        self._stepper = _instance_stepper

    def build_stepper(self) -> SystemProtocol:
        """
        Fail if called; this class should use the preset instance stepper.

        Raises:
            AssertionError: Always, because this hook should not be invoked.
        """
        msg = "build_stepper should not be called when `_stepper` is already set."
        raise AssertionError(msg)


@pytest.mark.parametrize("system", [DummySystem()])
def test_abstraction_error(system: SystemABC) -> None:
    """Test default stepper raises `NotImplementedError` when not overridden."""
    with pytest.raises(NotImplementedError):
        system.step(np.float64(0.0), np.array([1.0, 2.0, 3.0], dtype=np.float64))


def test_class_level_stepper_is_used() -> None:
    """Test class-level `_stepper` is used when no dynamic builder is defined."""
    system = ClassStepperSystem()
    result = system.step(
        np.float64(2.0), np.array([1.0, 2.0, 3.0], dtype=np.float64), offset=1.0
    )
    expected = np.array([4.0, 6.0, 8.0], dtype=np.float64)
    np.testing.assert_array_equal(result, expected)


def test_build_stepper_hook_constructs_stepper_once() -> None:
    """Test `build_stepper` is called once and cached for subsequent steps."""
    system = DynamicBuilderSystem()
    result_1 = system.step(
        np.float64(2.0), np.array([1.0, 2.0, 3.0], dtype=np.float64), scale=3.0
    )
    result_2 = system.step(
        np.float64(1.0), np.array([1.0, 2.0, 3.0], dtype=np.float64), scale=2.0
    )

    np.testing.assert_array_equal(result_1, np.array([7.0, 8.0, 9.0], dtype=np.float64))
    np.testing.assert_array_equal(result_2, np.array([3.0, 4.0, 5.0], dtype=np.float64))
    assert system.build_stepper_calls == 1


def test_build_preserves_existing_instance_stepper() -> None:
    """Test pre-set instance `_stepper` takes precedence over `build_stepper`."""
    system = PresetInstanceStepperSystem().build()
    result = system.step(np.float64(2.0), np.array([1.0, 2.0, 3.0], dtype=np.float64))
    expected = np.array([3.0, 4.0, 5.0], dtype=np.float64)
    np.testing.assert_array_equal(result, expected)
