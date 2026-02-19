"""Unit tests for the `CategoricalAxisModel` class."""

import pytest
from pydantic import ValidationError

from flepimop2.configuration._axes import Axis, CategoricalAxisModel


@pytest.mark.parametrize(
    "labels",
    [
        ("foo", "bar", "baz"),
        ("mild", "moderate", "severe"),
        ("a",),
    ],
)
def test_categorical_axis_model_valid_no_values(labels: tuple[str, ...]) -> None:
    """Test that valid categorical axes without values are accepted."""
    m = CategoricalAxisModel(labels=labels)
    assert m.kind == "categorical"
    assert m.labels == labels
    assert m.values is None


@pytest.mark.parametrize(
    ("labels", "values"),
    [
        (("mild", "moderate", "severe"), (1.0, 3.0, 7.0)),
        (("a", "b"), (0.0, 1.0)),
        (("x",), (42.0,)),
    ],
)
def test_categorical_axis_model_valid_with_values(
    labels: tuple[str, ...], values: tuple[float, ...]
) -> None:
    """Test that categorical axes with matching values are accepted."""
    m = CategoricalAxisModel(labels=labels, values=values)
    assert m.values == values


@pytest.mark.parametrize(
    ("labels", "values"),
    [
        (("a", "b"), (1.0, 2.0, 3.0)),  # too many values
        (("a", "b", "c"), (1.0,)),  # too few values
    ],
)
def test_categorical_axis_model_values_length_mismatch_raises(
    labels: tuple[str, ...], values: tuple[float, ...]
) -> None:
    """Test that mismatched labels/values lengths raise ValidationError."""
    with pytest.raises(ValidationError, match="must match"):
        CategoricalAxisModel(labels=labels, values=values)


def test_categorical_axis_model_empty_labels_raises() -> None:
    """Test that an empty labels tuple raises ValidationError."""
    with pytest.raises(ValidationError):
        CategoricalAxisModel(labels=())


def test_categorical_axis_model_to_axis_no_values() -> None:
    """Test that `to_axis` returns None for values when none were supplied."""
    ax = CategoricalAxisModel(labels=("foo", "bar")).to_axis("group")
    assert ax.name == "group"
    assert ax.kind == "categorical"
    assert ax.labels == ("foo", "bar")
    assert ax.values is None


@pytest.mark.parametrize(
    ("labels", "values"),
    [
        (("mild", "moderate", "severe"), (1.0, 3.0, 7.0)),
        (("a", "b"), (0.0, 1.0)),
    ],
)
def test_categorical_axis_model_to_axis_with_values(
    labels: tuple[str, ...], values: tuple[float, ...]
) -> None:
    """Test that `to_axis` propagates supplied values onto the `Axis`."""
    ax = CategoricalAxisModel(labels=labels, values=values).to_axis("x")
    assert ax.values == values


def test_categorical_axis_model_to_axis_returns_axis_named_tuple() -> None:
    """Test that `to_axis` returns an `Axis` NamedTuple."""
    ax = CategoricalAxisModel(labels=("a", "b")).to_axis("demo")
    assert isinstance(ax, Axis)
    assert isinstance(ax, tuple)


def test_categorical_axis_model_to_axis_name() -> None:
    """Test that the name argument is set on the returned `Axis`."""
    ax = CategoricalAxisModel(labels=("foo", "bar", "fizz", "buzz")).to_axis(
        "axes_name_one"
    )
    assert ax.name == "axes_name_one"
    assert ax.kind == "categorical"
