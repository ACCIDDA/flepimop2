"""Unit tests for the `YamlSerializableBaseModel` class."""

from pathlib import Path

import pytest

from flepimop2.configuration._yaml import YamlSerializableBaseModel


class SimpleModel(YamlSerializableBaseModel):
    """Simple test model with basic types."""

    name: str
    count: int


class ComplexModel(YamlSerializableBaseModel):
    """Test model with nested list of models."""

    name: str
    items: list[SimpleModel]
    metadata: dict[str, str]


@pytest.mark.parametrize(
    ("model_class", "instance"),
    [
        (SimpleModel, SimpleModel(name="test", count=42)),
        (
            ComplexModel,
            ComplexModel(
                name="complex_test",
                items=[
                    SimpleModel(name="item1", count=5),
                    SimpleModel(name="item2", count=7),
                ],
                metadata={"key1": "value1", "key2": "value2"},
            ),
        ),
    ],
)
def test_yaml_serialization_round_trip(
    model_class: type[YamlSerializableBaseModel],
    instance: YamlSerializableBaseModel,
    tmp_path: Path,
) -> None:
    """Test that serializing and deserializing returns an equivalent object."""
    yaml_file = tmp_path / "test.yaml"
    instance.to_yaml(yaml_file)
    loaded = model_class.from_yaml(yaml_file)
    assert loaded == instance
