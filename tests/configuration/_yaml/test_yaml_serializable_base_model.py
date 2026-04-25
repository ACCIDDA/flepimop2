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
