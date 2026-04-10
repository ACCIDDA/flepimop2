"""Tests for runtime fixed-parameter sampling."""

from typing import Any

import numpy as np
import pytest

from flepimop2.axis import AxisCollection
from flepimop2.parameter.abc import ParameterRequest
from flepimop2.parameter.fixed import FixedParameter


@pytest.mark.parametrize("value", [42.0, 123.45])
def test_fixed_parameter_returns_scalar_parameter_value(value: float) -> None:
    """Scalar fixed parameters should resolve to scalar runtime samples."""
    sample = FixedParameter(value=value).sample()
    assert sample.shape.axis_names == ()
    assert sample.shape.sizes == ()
    assert sample.item() == value


@pytest.mark.parametrize(
    ("axes_config", "value"),
    [
        ({"age": {"kind": "categorical", "labels": ["0-17", "18-64", "65+"]}}, 0.1),
        ({"region": {"kind": "categorical", "labels": ["north", "south"]}}, 0.2),
        (
            {
                "age": {
                    "kind": "continuous",
                    "size": 10,
                    "domain": (18, 65),
                    "spacing": "linear",
                }
            },
            0.3,
        ),
    ],
)
def test_fixed_parameter_broadcasts_scalar_to_requested_shape(
    axes_config: dict[str, Any], value: float
) -> None:
    """Scalar fixed parameters can broadcast to system-requested shapes."""
    axes_name = next(iter(axes_config.keys()))
    axes = AxisCollection.from_config(axes_config)
    sample = FixedParameter(value=value).sample(
        axes=axes,
        request=ParameterRequest(name="gamma", axes=(axes_name,), broadcast=True),
    )
    assert sample.shape.axis_names == (axes_name,)
    np.testing.assert_array_equal(sample.value, np.repeat(value, axes.size(axes_name)))


def test_fixed_parameter_rejects_non_scalar_without_shape_context() -> None:
    """Array-valued fixed parameters need explicit named shape information."""
    with pytest.raises(
        ValueError,
        match=(
            r"^Non-scalar FixedParameter values require either an "
            r"explicit 'shape' configuration or a system request.$"
        ),
    ):
        FixedParameter(value=[1.0, 2.0]).sample()


def test_fixed_parameter_rejects_conflicting_configured_and_requested_shapes() -> None:
    """Explicit parameter shape must match the system-requested shape."""
    axes = AxisCollection.from_config({
        "age": {"kind": "categorical", "labels": ["0-17", "18-64", "65+"]},
        "region": {"kind": "categorical", "labels": ["north", "south"]},
    })

    with pytest.raises(
        ValueError,
        match=(
            r"^FixedParameter shape \('age',\) does not match requested "
            r"shape \('region',\) for parameter 'beta'\.$"
        ),
    ):
        FixedParameter(value=[0.1, 0.2, 0.3], shape=("age",)).sample(
            axes=axes,
            request=ParameterRequest(name="beta", axes=("region",)),
        )


def test_fixed_parameter_rejects_value_with_incompatible_resolved_shape() -> None:
    """Configured values must match or broadcast to the resolved named shape."""
    axes = AxisCollection.from_config({
        "age": {"kind": "categorical", "labels": ["0-17", "18-64", "65+"]}
    })

    with pytest.raises(
        ValueError,
        match=(
            r"^FixedParameter value shape \(2,\) is not compatible with "
            r"resolved shape \(3,\) for axes \('age',\)\.$"
        ),
    ):
        FixedParameter(value=[0.1, 0.2], shape=("age",)).sample(axes=axes)
