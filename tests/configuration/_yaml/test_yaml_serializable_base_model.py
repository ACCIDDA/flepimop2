# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Unit tests for the `YamlSerializableBaseModel` class."""

from pathlib import Path

import pytest

from flepimop2.configuration._yaml import (
    YamlSerializableBaseModel,
    yaml_mapping,
    yaml_sequence,
)


class SimpleModel(YamlSerializableBaseModel):
    """Simple test model with basic types."""

    name: str
    count: int


class ComplexModel(YamlSerializableBaseModel):
    """Test model with nested list of models."""

    name: str
    items: list[SimpleModel]
    metadata: dict[str, str]


class StyledModel(YamlSerializableBaseModel):
    """Test model that requests flow-style YAML for specific subtrees."""

    name: str
    items: list[int]
    metadata: dict[str, str]

    def to_yaml_data(self) -> object:
        """
        Serialize selected subtrees with explicit YAML style wrappers.

        Returns:
            A YAML-ready mapping with explicit flow-style wrappers.
        """
        return {
            "name": self.name,
            "items": yaml_sequence(self.items, flow_style=True),
            "metadata": yaml_mapping(self.metadata, flow_style=True),
        }


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
def test_yaml_safe_dump_and_safe_load_round_trip(
    model_class: type[YamlSerializableBaseModel],
    instance: YamlSerializableBaseModel,
) -> None:
    """Text-level YAML helpers should round-trip models without file I/O."""
    dumped = instance.safe_dump()
    loaded = model_class.safe_load(dumped)
    assert loaded == instance


def test_yaml_safe_dump_supports_flow_style_wrappers() -> None:
    """Wrapped subtrees should retain their requested YAML flow style."""
    instance = StyledModel(name="styled", items=[1, 2], metadata={"a": "b"})

    dumped = instance.safe_dump()

    assert dumped == "name: styled\nitems: [1, 2]\nmetadata: {a: b}\n"
