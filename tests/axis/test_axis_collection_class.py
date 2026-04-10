"""Tests for `AxisCollection` runtime behavior."""

from typing import Any

import pytest

from flepimop2.axis import Axis, AxisCollection, ResolvedShape


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (
            {
                "age": {
                    "kind": "categorical",
                    "labels": ["0-17", "18-64", "65+"],
                },
                "time": {
                    "kind": "continuous",
                    "domain": (0.0, 10.0),
                    "size": 4,
                },
            },
            {
                "names": ("age", "time"),
                "size_queries": ("age", "time"),
                "sizes": (3, 4),
                "label_query": "age",
                "labels": ("0-17", "18-64", "65+"),
            },
        ),
        (
            {
                "region": {
                    "kind": "categorical",
                    "labels": ["A", "B"],
                },
                "severity": {
                    "kind": "categorical",
                    "labels": ["low", "high"],
                },
            },
            {
                "names": ("region", "severity"),
                "size_queries": ("region", "severity"),
                "sizes": (2, 2),
                "label_query": "region",
                "labels": ("A", "B"),
            },
        ),
    ],
)
def test_axis_collection_loads_axes_from_config(
    config: dict[str, dict[str, Any]],
    expected: dict[str, Any],
) -> None:
    """AxisCollection should preserve configured axis metadata."""
    axes = AxisCollection.from_config(config)

    expected_names = expected["names"]
    size_queries = expected["size_queries"]
    expected_sizes = expected["sizes"]
    label_query = expected["label_query"]
    expected_labels = expected["labels"]

    assert isinstance(expected_names, tuple)
    assert isinstance(size_queries, tuple)
    assert isinstance(expected_sizes, tuple)
    assert isinstance(label_query, str)
    assert isinstance(expected_labels, tuple)

    assert len(axes) == len(expected_names)
    assert tuple(axes) == expected_names
    assert axes.sizes(*size_queries) == expected_sizes
    assert axes[label_query].labels == expected_labels


@pytest.mark.parametrize(
    ("axes", "axis_names", "expected_shape"),
    [
        (
            AxisCollection({
                "region": Axis(
                    name="region",
                    kind="categorical",
                    size=2,
                    labels=("A", "B"),
                ),
                "age": Axis(
                    name="age",
                    kind="categorical",
                    size=3,
                    labels=("0-17", "18-64", "65+"),
                ),
            }),
            ("region", "age"),
            ResolvedShape(axis_names=("region", "age"), sizes=(2, 3)),
        ),
        (
            AxisCollection({
                "time": Axis(
                    name="time",
                    kind="continuous",
                    size=4,
                    domain=(0.0, 8.0),
                    spacing="linear",
                ),
            }),
            ("time",),
            ResolvedShape(axis_names=("time",), sizes=(4,)),
        ),
        (
            AxisCollection({
                "region": Axis(
                    name="region",
                    kind="categorical",
                    size=2,
                    labels=("A", "B"),
                ),
                "age": Axis(
                    name="age",
                    kind="categorical",
                    size=3,
                    labels=("0-17", "18-64", "65+"),
                ),
                "time": Axis(
                    name="time",
                    kind="continuous",
                    size=5,
                    domain=(0.0, 10.0),
                    spacing="linear",
                ),
            }),
            ("region", "age", "time"),
            ResolvedShape(axis_names=("region", "age", "time"), sizes=(2, 3, 5)),
        ),
    ],
)
def test_axis_collection_resolves_named_shapes(
    axes: AxisCollection,
    axis_names: tuple[str, ...],
    expected_shape: ResolvedShape,
) -> None:
    """AxisCollection should resolve axis names into a concrete named shape."""
    assert axes.resolve_shape(axis_names) == expected_shape


@pytest.mark.parametrize(
    ("axes", "axis_names"),
    [
        (
            AxisCollection({
                "age": Axis(
                    name="age",
                    kind="categorical",
                    size=3,
                    labels=("0-17", "18-64", "65+"),
                )
            }),
            ("region",),
        ),
        (
            AxisCollection({
                "region": Axis(
                    name="region",
                    kind="categorical",
                    size=2,
                    labels=("A", "B"),
                ),
                "age": Axis(
                    name="age",
                    kind="categorical",
                    size=3,
                    labels=("0-17", "18-64", "65+"),
                ),
            }),
            ("region", "time"),
        ),
    ],
)
def test_axis_collection_rejects_unknown_axis_names(
    axes: AxisCollection,
    axis_names: tuple[str, ...],
) -> None:
    """AxisCollection should raise when asked to resolve unknown axes."""
    with pytest.raises(KeyError, match="Unknown axis names requested"):
        axes.resolve_shape(axis_names)
