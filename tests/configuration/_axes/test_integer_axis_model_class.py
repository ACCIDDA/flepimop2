"""Unit tests for the `IntegerAxisModel` class."""

from typing import Literal

import pytest
from pydantic import ValidationError

from flepimop2.configuration._axes import Axis, IntegerAxisModel


@pytest.mark.parametrize(
    ("domain", "size", "spacing"),
    [
        ((0, 10), None, "linear"),
        ((0, 70), None, "linear"),
        ((1, 100), 5, "log"),
        ((0, 10), 3, "linear"),
    ],
)
def test_integer_axis_model_valid(
    domain: tuple[int, int], size: int | None, spacing: Literal["linear", "log"]
) -> None:
    """Test that valid integer axis configurations are accepted."""
    m = IntegerAxisModel(domain=domain, size=size, spacing=spacing)
    assert m.kind == "integer"
    assert m.domain == domain
    assert m.size == size
    assert m.spacing == spacing


def test_integer_axis_model_defaults() -> None:
    """Test that size defaults to None and spacing defaults to 'linear'."""
    m = IntegerAxisModel(domain=(0, 10))
    assert m.size is None
    assert m.spacing == "linear"


@pytest.mark.parametrize(
    ("domain", "size", "spacing"),
    [
        ((10, 0), None, "linear"),  # reversed domain
        ((5, 5), None, "linear"),  # equal bounds
        ((0, 10), 1, "linear"),  # size not > 1
        ((0, 10), 3, "log"),  # log with zero lower bound
        ((-5, 10), 3, "log"),  # log with negative lower bound
    ],
)
def test_integer_axis_model_invalid(
    domain: tuple[int, int], size: int | None, spacing: Literal["linear", "log"]
) -> None:
    """Test that invalid integer axis configurations raise ValidationError."""
    with pytest.raises(ValidationError):
        IntegerAxisModel(domain=domain, size=size, spacing=spacing)


@pytest.mark.parametrize(
    ("domain", "expected_labels", "expected_values"),
    [
        ((0, 5), ("0", "1", "2", "3", "4", "5"), (0, 1, 2, 3, 4, 5)),
        ((3, 6), ("3", "4", "5", "6"), (3, 4, 5, 6)),
    ],
)
def test_integer_axis_model_to_axis_all_integers(
    domain: tuple[int, int],
    expected_labels: tuple[str, ...],
    expected_values: tuple[int, ...],
) -> None:
    """Test that size=None enumerates every integer in [lo, hi] inclusive."""
    ax = IntegerAxisModel(domain=domain).to_axis("age")
    assert ax.labels == expected_labels
    assert ax.values == expected_values


def test_integer_axis_model_to_axis_with_size_endpoints() -> None:
    """Test that providing a size still preserves domain endpoints after rounding."""
    ax = IntegerAxisModel(domain=(0, 10), size=3).to_axis("coarse")
    assert ax.values is not None
    assert ax.values[0] == 0
    assert ax.values[-1] == 10
    assert len(ax.values) == 3


def test_integer_axis_model_to_axis_log_endpoints() -> None:
    """Test that log spacing preserves endpoints."""
    ax = IntegerAxisModel(domain=(1, 100), size=3, spacing="log").to_axis("log_int")
    assert ax.values is not None
    assert ax.values[0] == 1
    assert ax.values[-1] == 100


def test_integer_axis_model_to_axis_labels_are_strings() -> None:
    """Test that all labels produced by `to_axis` are strings."""
    ax = IntegerAxisModel(domain=(0, 3)).to_axis("x")
    assert all(isinstance(lbl, str) for lbl in ax.labels)


def test_integer_axis_model_to_axis_values_are_ints() -> None:
    """Test that all values produced by `to_axis` are ints."""
    ax = IntegerAxisModel(domain=(0, 3)).to_axis("x")
    assert ax.values is not None
    assert all(isinstance(v, int) for v in ax.values)


def test_integer_axis_model_to_axis_returns_axis_named_tuple() -> None:
    """Test that `to_axis` returns an `Axis` NamedTuple."""
    ax = IntegerAxisModel(domain=(0, 1)).to_axis("demo")
    assert isinstance(ax, Axis)
    assert isinstance(ax, tuple)


def test_integer_axis_model_to_axis_name() -> None:
    """Test that the name argument is set on the returned `Axis`."""
    ax = IntegerAxisModel(domain=(0, 5)).to_axis("ages")
    assert ax.name == "ages"
    assert ax.kind == "integer"
