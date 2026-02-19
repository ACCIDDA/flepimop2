"""Unit tests for the `AxisModel` discriminated union and `AxesGroupModel` type."""

from typing import Final

import pytest
from pydantic import TypeAdapter, ValidationError

from flepimop2.configuration import ConfigurationModel
from flepimop2.configuration._axes import (
    AxesGroupModel,
    AxisModel,
    CategoricalAxisModel,
    ContinuousAxisModel,
    IntegerAxisModel,
)

AXIS_MODEL_ADAPTER: Final[TypeAdapter[AxisModel]] = TypeAdapter(AxisModel)
AXES_GROUP_ADAPTER: Final[TypeAdapter[AxesGroupModel]] = TypeAdapter(AxesGroupModel)


@pytest.mark.parametrize(
    ("data", "expected_type"),
    [
        (
            {"kind": "continuous", "domain": [0.0, 1.0], "size": 5},
            ContinuousAxisModel,
        ),
        (
            {"kind": "integer", "domain": [0, 10]},
            IntegerAxisModel,
        ),
        (
            {"kind": "categorical", "labels": ["a", "b"]},
            CategoricalAxisModel,
        ),
    ],
)
def test_axis_model_valid_kinds(data: dict[str, object], expected_type: type) -> None:
    """Test that each valid `kind` value parses to the correct model type."""
    model = AXIS_MODEL_ADAPTER.validate_python(data)
    assert isinstance(model, expected_type)
    assert model.kind == data["kind"]


def test_axis_model_unknown_kind_raises() -> None:
    """Test that an unknown `kind` value raises ValidationError."""
    with pytest.raises(ValidationError):
        AXIS_MODEL_ADAPTER.validate_python({"kind": "ordinal", "labels": ["a", "b"]})


def test_axis_model_missing_kind_raises() -> None:
    """Test that omitting `kind` raises ValidationError."""
    with pytest.raises(ValidationError):
        AXIS_MODEL_ADAPTER.validate_python({"labels": ["a", "b"]})


def test_axes_group_model_parses_mixed_axes() -> None:
    """Test that a dict with all three axis kinds validates correctly."""
    data = {
        "space_x": {"kind": "continuous", "domain": [0.0, 12.0], "size": 20},
        "ages": {"kind": "integer", "domain": [0, 70]},
        "group": {"kind": "categorical", "labels": ["foo", "bar"]},
    }
    result = AXES_GROUP_ADAPTER.validate_python(data)
    assert set(result.keys()) == {"space_x", "ages", "group"}
    assert isinstance(result["space_x"], ContinuousAxisModel)
    assert isinstance(result["ages"], IntegerAxisModel)
    assert isinstance(result["group"], CategoricalAxisModel)


def test_axes_group_model_invalid_key_raises() -> None:
    """Test that a key that is not a valid IdentifierString raises ValidationError."""
    with pytest.raises(ValidationError):
        AXES_GROUP_ADAPTER.validate_python({
            "InvalidKey": {"kind": "categorical", "labels": ["a"]}
        })


def test_axes_group_model_to_axis_round_trip() -> None:
    """Test that models in AxesGroupModel can be converted to Axis via to_axis."""
    result = AXES_GROUP_ADAPTER.validate_python({
        "age": {"kind": "integer", "domain": [0, 5]}
    })
    ax = result["age"].to_axis("age")
    assert ax.name == "age"
    assert ax.labels == ("0", "1", "2", "3", "4", "5")


def test_configuration_model_axes_defaults_to_empty_dict() -> None:
    """Test that axes defaults to an empty dict when omitted from config."""
    cfg = ConfigurationModel.model_validate({})
    assert cfg.axes == {}


@pytest.mark.parametrize(
    ("key", "data", "expected_kind"),
    [
        (
            "age",
            {"kind": "integer", "domain": [0, 10]},
            "integer",
        ),
        (
            "severity",
            {"kind": "categorical", "labels": ["mild", "severe"], "values": [1.0, 5.0]},
            "categorical",
        ),
        (
            "space_x",
            {"kind": "continuous", "domain": [0.0, 12.0], "size": 10},
            "continuous",
        ),
    ],
)
def test_configuration_model_axes_parsed(
    key: str, data: dict[str, object], expected_kind: str
) -> None:
    """
    Test that each axis kind is correctly parsed when embedded in `ConfigurationModel`.

    Args:
        key: The axis name (i.e. the dict key from the config).
        data: The axis configuration dict.
        expected_kind: The expected `kind` value of the parsed model.

    """
    cfg = ConfigurationModel.model_validate({"axes": {key: data}})
    assert key in cfg.axes
    assert cfg.axes[key].kind == expected_kind
