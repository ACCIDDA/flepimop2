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
"""Tests for parameter-oriented `ConfigurationModel` behavior."""

from pathlib import Path

import pytest

from flepimop2.configuration import ConfigurationModel
from flepimop2.parameter.abc import build as build_parameter


@pytest.mark.parametrize(
    ("key", "value", "expected"),
    [("parameter", 0.3, "fixed(0.3)"), ("parameters", 2, "fixed(2)")],
)
def test_configuration_model_rewrites_numeric_parameter_values(
    key: str, value: float, expected: str
) -> None:
    """Bare numeric parameter values should become fixed-parameter shorthand."""
    configuration = ConfigurationModel.model_validate({key: {"beta": value}})

    assert configuration.parameters["beta"] == expected
    assert build_parameter(
        configuration.parameters["beta"]
    ).sample().item() == pytest.approx(value)


def test_configuration_model_from_yaml_accepts_numeric_parameter_values(
    tmp_path: Path,
) -> None:
    """YAML config files should accept singular `parameter` with bare numerics."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("parameter:\n  beta: 0.3\n", encoding="utf-8")

    configuration = ConfigurationModel.from_yaml(config_path)

    assert configuration.parameters["beta"] == "fixed(0.3)"
