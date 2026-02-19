"""Unit tests for the `CategoricalAxisModel` class."""

import pytest
from pydantic import ValidationError

from flepimop2.configuration._axes import CategoricalAxisModel


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
    assert m.values == tuple(range(1, len(labels) + 1))


@pytest.mark.parametrize(
    ("labels", "values"),
    [
        (("mild", "moderate", "severe"), (1, 3, 7)),
        (("a", "b"), (0, 1)),
        (("x",), (42,)),
    ],
)
def test_categorical_axis_model_valid_with_values(
    labels: tuple[str, ...], values: tuple[int, ...]
) -> None:
    """Test that categorical axes with matching values are accepted."""
    m = CategoricalAxisModel(labels=labels, values=values)
    assert m.values == values


@pytest.mark.parametrize(
    ("labels", "values"),
    [
        (("a", "b"), (1, 2, 3)),  # too many values
        (("a", "b", "c"), (1,)),  # too few values
    ],
)
def test_categorical_axis_model_values_length_mismatch_raises(
    labels: tuple[str, ...], values: tuple[int, ...]
) -> None:
    """Test that mismatched labels/values lengths raise ValidationError."""
    with pytest.raises(ValidationError, match="must match"):
        CategoricalAxisModel(labels=labels, values=values)


def test_categorical_axis_model_empty_labels_raises() -> None:
    """Test that an empty labels tuple raises ValidationError."""
    with pytest.raises(ValidationError):
        CategoricalAxisModel(labels=())
