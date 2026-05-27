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
"""Tests for configuration YAML formatting."""

from yaml import safe_load

from flepimop2.configuration import ConfigurationModel


def test_configuration_model_safe_dump_omits_empty_sections_and_name() -> None:
    """Formatted YAML should omit empty top-level sections and blank names."""
    configuration = ConfigurationModel.model_validate({
        "name": "",
        "engines": {
            "default": {
                "module": "demo.engine",
                "options": {},
            }
        },
        "systems": {},
    })

    dumped = configuration.safe_dump()

    assert safe_load(dumped) == {"engines": [{"module": "demo.engine"}]}


def test_configuration_model_safe_dump_list_view_round_trips_default_sections() -> None:
    """Single default entries should serialize as a one-item list view."""
    configuration = ConfigurationModel.model_validate({
        "engines": {
            "default": {
                "module": "demo.engine",
            }
        }
    })

    dumped = configuration.safe_dump()
    loaded = ConfigurationModel.safe_load(dumped)

    assert dumped == "engines:\n- module: demo.engine\n"
    engine = loaded.engines["default"]
    assert not isinstance(engine, str)
    assert engine.module == "demo.engine"


def test_configuration_model_safe_dump_omits_empty_simulate_fields() -> None:
    """Formatted YAML should omit empty `params` and null `scenario` fields."""
    configuration = ConfigurationModel.model_validate({
        "engines": {"default": {"module": "demo.engine"}},
        "systems": {"default": {"module": "demo.system"}},
        "backends": {"default": {"module": "demo.backend"}},
        "simulate": {
            "main": {
                "times": [0.0, 1.0],
                "params": {},
                "scenario": None,
            }
        },
    })

    dumped = configuration.safe_dump()

    assert safe_load(dumped) == {
        "engines": [{"module": "demo.engine"}],
        "systems": [{"module": "demo.system"}],
        "backends": [{"module": "demo.backend"}],
        "simulate": {
            "main": {
                "engine": "default",
                "system": "default",
                "backend": "default",
                "times": [0.0, 1.0],
            }
        },
    }


def test_configuration_model_safe_dump_orders_sections_consistently() -> None:
    """Formatted YAML should emit top-level sections in canonical order."""
    configuration = ConfigurationModel.model_validate({
        "simulate": {
            "main": {
                "times": [0.0, 1.0],
            }
        },
        "parameters": {
            "beta": "fixed(0.3)",
        },
        "backends": {"default": {"module": "demo.backend"}},
        "axes": {
            "age": {
                "kind": "categorical",
                "labels": ["child", "adult"],
            }
        },
        "engines": {"default": {"module": "demo.engine"}},
        "systems": {"default": {"module": "demo.system"}},
        "name": "demo",
    })

    dumped = configuration.safe_dump()

    assert dumped.splitlines() == [
        "name: demo",
        "axes:",
        "  age:",
        "    kind: categorical",
        "    labels:",
        "      - child",
        "      - adult",
        "    values:",
        "      - 1",
        "      - 2",
        "engines:",
        "- module: demo.engine",
        "systems:",
        "- module: demo.system",
        "backends:",
        "- module: demo.backend",
        "parameters:",
        "  beta: 0.3",
        "simulate:",
        "  main:",
        "    engine: default",
        "    system: default",
        "    backend: default",
        "    times:",
        "      - 0.0",
        "      - 1.0",
    ]
