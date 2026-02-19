"""Unit tests for the `ContinuousAxisModel` class."""

from typing import Literal

import pytest
from pydantic import ValidationError

from flepimop2.configuration._axes import Axis, ContinuousAxisModel


@pytest.mark.parametrize(
    ("domain", "size", "spacing"),
    [
        ((0.0, 1.0), 2, "linear"),
        ((1.0, 100.0), 5, "log"),
        ((0.0, 12.0), 20, "linear"),
    ],
)
def test_continuous_axis_model_valid(
    domain: tuple[float, float], size: int, spacing: Literal["linear", "log"]
) -> None:
    """Test that valid continuous axis configurations are accepted."""
    m = ContinuousAxisModel(domain=domain, size=size, spacing=spacing)
    assert m.kind == "continuous"
    assert m.domain == domain
    assert m.size == size
    assert m.spacing == spacing


def test_continuous_axis_model_default_spacing() -> None:
    """Test that spacing defaults to 'linear'."""
    m = ContinuousAxisModel(domain=(0.0, 1.0), size=2)
    assert m.spacing == "linear"


@pytest.mark.parametrize(
    ("domain", "size", "spacing"),
    [
        ((5.0, 0.0), 3, "linear"),  # reversed domain
        ((1.0, 1.0), 3, "linear"),  # equal bounds
        ((0.0, 1.0), 1, "linear"),  # size not > 1
        ((0.0, 10.0), 3, "log"),  # log with non-positive lower bound
        ((-1.0, 10.0), 3, "log"),  # log with negative lower bound
    ],
)
def test_continuous_axis_model_invalid(
    domain: tuple[float, float], size: int, spacing: Literal["linear", "log"]
) -> None:
    """Test that invalid continuous axis configurations raise ValidationError."""
    with pytest.raises(ValidationError):
        ContinuousAxisModel(domain=domain, size=size, spacing=spacing)


@pytest.mark.parametrize(
    ("domain", "size", "expected_first", "expected_last"),
    [
        ((0.0, 4.0), 5, 0.0, 4.0),
        ((0.0, 12.0), 5, 0.0, 12.0),
        ((-1.0, 1.0), 3, -1.0, 1.0),
    ],
)
def test_continuous_axis_model_to_axis_linear_endpoints(
    domain: tuple[float, float], size: int, expected_first: float, expected_last: float
) -> None:
    """Test that linear spacing produces correct endpoints."""
    ax = ContinuousAxisModel(domain=domain, size=size).to_axis("x")
    assert ax.values is not None
    assert ax.values[0] == pytest.approx(expected_first)
    assert ax.values[-1] == pytest.approx(expected_last)


def test_continuous_axis_model_to_axis_log_values() -> None:
    """Test that log spacing produces geometrically-spaced values."""
    ax = ContinuousAxisModel(domain=(1.0, 100.0), size=3, spacing="log").to_axis("x")
    assert ax.values is not None
    assert ax.values[0] == pytest.approx(1.0)
    assert ax.values[1] == pytest.approx(10.0)
    assert ax.values[-1] == pytest.approx(100.0)


def test_continuous_axis_model_to_axis_size() -> None:
    """Test that `to_axis` produces the requested number of points."""
    m = ContinuousAxisModel(domain=(0.0, 1.0), size=7)
    ax = m.to_axis("x")
    assert len(ax.labels) == 7
    assert len(ax.values) == 7  # type: ignore[arg-type]


def test_continuous_axis_model_to_axis_labels_are_strings() -> None:
    """Test that all labels produced by `to_axis` are strings."""
    ax = ContinuousAxisModel(domain=(0.0, 1.0), size=4).to_axis("x")
    assert all(isinstance(lbl, str) for lbl in ax.labels)


def test_continuous_axis_model_to_axis_values_are_floats() -> None:
    """Test that all values produced by `to_axis` are floats."""
    ax = ContinuousAxisModel(domain=(0.0, 1.0), size=4).to_axis("x")
    assert ax.values is not None
    assert all(isinstance(v, float) for v in ax.values)


def test_continuous_axis_model_to_axis_returns_axis_named_tuple() -> None:
    """Test that `to_axis` returns an `Axis` NamedTuple."""
    ax = ContinuousAxisModel(domain=(0.0, 1.0), size=2).to_axis("demo")
    assert isinstance(ax, Axis)
    assert isinstance(ax, tuple)


def test_continuous_axis_model_to_axis_name() -> None:
    """Test that the name argument is set on the returned `Axis`."""
    ax = ContinuousAxisModel(domain=(0.0, 1.0), size=2).to_axis("space_x")
    assert ax.name == "space_x"
    assert ax.kind == "continuous"
