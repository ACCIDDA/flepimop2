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
"""Examples and tests for overriding `ModuleBase.to_yaml_data`."""

from flepimop2.module import ModuleBase
from flepimop2.yaml import (
    YamlFormattedMapping,
    YamlFormattedSequence,
    YamlSerializableBaseModel,
    yaml_mapping,
    yaml_sequence,
)


class StyledModule(ModuleBase, module="flepimop2.test.styled"):
    """Example module that customizes how its YAML subtree is emitted."""

    labels: tuple[str, ...]
    bounds: tuple[int, int]
    metadata: dict[str, str] | None = None

    def to_yaml_data(self) -> object:
        """
        Serialize selected fields with explicit YAML style wrappers.

        Returns:
            A YAML-ready mapping with flow-style wrappers for selected fields.
        """
        data = super().to_yaml_data()
        assert isinstance(data, dict)
        data["labels"] = yaml_sequence(self.labels, flow_style=True)
        data["bounds"] = yaml_sequence(self.bounds, flow_style=True)
        if self.metadata:
            data["metadata"] = yaml_mapping(self.metadata, flow_style=True)
        return data


class MixedStyleModule(ModuleBase, module="flepimop2.test.mixed-style"):
    """Example module that mixes flow-style and block-style YAML output."""

    title: str
    dims: tuple[int, int]
    steps: tuple[dict[str, str], ...]

    def to_yaml_data(self) -> object:
        """
        Serialize simple values inline while keeping complex structures expanded.

        Returns:
            A YAML-ready mapping with both flow-style and block-style wrappers.
        """
        data = super().to_yaml_data()
        assert isinstance(data, dict)
        data["dims"] = yaml_sequence(self.dims, flow_style=True)
        data["steps"] = yaml_sequence(
            (yaml_mapping(step, flow_style=False) for step in self.steps),
            flow_style=False,
        )
        return data


class ModuleDocument(YamlSerializableBaseModel):
    """Simple wrapper model for testing module YAML output."""

    module: StyledModule


def test_module_to_yaml_data_override_can_customize_field_styles() -> None:
    """Module overrides can replace fields with explicit YAML style wrappers."""
    module = StyledModule(
        labels=("susceptible", "infected"),
        bounds=(0, 10),
        metadata={"kind": "demo"},
    )

    data = module.to_yaml_data()

    assert isinstance(data, dict)
    assert data["module"] == "flepimop2.test.styled"
    assert "options" not in data
    assert isinstance(data["labels"], YamlFormattedSequence)
    assert isinstance(data["bounds"], YamlFormattedSequence)
    assert isinstance(data["metadata"], YamlFormattedMapping)
    assert data == {
        "module": "flepimop2.test.styled",
        "labels": ["susceptible", "infected"],
        "bounds": [0, 10],
        "metadata": {"kind": "demo"},
    }


def test_module_to_yaml_data_override_changes_rendered_yaml() -> None:
    """Module overrides should affect the final YAML representation."""
    document = ModuleDocument(
        module=StyledModule(
            labels=("susceptible", "infected"),
            bounds=(0, 10),
            metadata={"kind": "demo"},
        )
    )

    dumped = document.safe_dump()

    assert dumped == (
        "module:\n"
        "  module: flepimop2.test.styled\n"
        "  labels: [susceptible, infected]\n"
        "  bounds: [0, 10]\n"
        "  metadata: {kind: demo}\n"
    )


def test_module_to_yaml_data_override_can_preserve_block_style() -> None:
    """Module overrides can keep complex collections expanded in block style."""

    class MixedStyleDocument(YamlSerializableBaseModel):
        module: MixedStyleModule

    document = MixedStyleDocument(
        module=MixedStyleModule(
            title="pipeline",
            dims=(2, 3),
            steps=(
                {"name": "prepare", "tool": "demo.prepare"},
                {"name": "simulate", "tool": "demo.simulate"},
            ),
        )
    )

    dumped = document.safe_dump()

    assert dumped == (
        "module:\n"
        "  module: flepimop2.test.mixed-style\n"
        "  title: pipeline\n"
        "  dims: [2, 3]\n"
        "  steps:\n"
        "    - name: prepare\n"
        "      tool: demo.prepare\n"
        "    - name: simulate\n"
        "      tool: demo.simulate\n"
    )
