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
"""Tests for `ConfigurationModel.patch`."""

import math

import pytest

from flepimop2.configuration import ConfigurationModel
from flepimop2.typing import PatchConflictMode


def test_configuration_model_patch_merge_delegates_to_module_patch() -> None:
    """Merging configurations should patch overlapping module entries."""
    configuration = ConfigurationModel.model_validate({
        "parameters": {
            "foo": {
                "module": "fixed",
                "value": [1, 2, 3],
                "shape": "age",
            },
            "bar": {
                "module": "fixed",
                "value": 0.5,
            },
        }
    })
    patch = ConfigurationModel.model_validate({
        "parameters": {
            "foo": {
                "module": "fixed",
                "value": [4, 5, 6],
            },
            "baz": {
                "module": "fixed",
                "value": 0.7,
            },
        }
    })

    patched = configuration.patch(patch, conflict=PatchConflictMode.MERGE)
    assert patched.model_dump(exclude_none=True).get("parameters", {}) == {
        "foo": {
            "module": "fixed",
            "value": [4, 5, 6],
            "shape": "age",
        },
        "bar": {
            "module": "fixed",
            "value": 0.5,
        },
        "baz": {
            "module": "fixed",
            "value": 0.7,
        },
    }


def test_configuration_model_patch_replace_replaces_duplicate_entries() -> None:
    """Replace mode should overwrite duplicate section keys with patch values."""
    configuration = ConfigurationModel.model_validate({
        "parameters": {"pi": math.pi, "r0": 0.1}
    })
    patch = ConfigurationModel.model_validate({"parameters": {"gamma": 0.2, "r0": 0.3}})

    patched = configuration.patch(patch, conflict=PatchConflictMode.REPLACE)

    assert patched.parameters == {
        "pi": f"fixed({math.pi!r})",
        "gamma": "fixed(0.2)",
        "r0": "fixed(0.3)",
    }


def test_configuration_model_patch_merge_merges_simulate_models() -> None:
    """Non-module top-level models should use the default base-model merge."""
    configuration = ConfigurationModel.model_validate({
        "engines": {"default": {"module": "demo.engine"}},
        "systems": {"default": {"module": "demo.system"}},
        "backends": {"default": {"module": "demo.backend"}},
        "simulate": {
            "main": {
                "times": [0.0, 1.0],
                "params": {"alpha": 1.0},
            }
        },
    })
    patch = ConfigurationModel.model_validate({
        "engines": {"default": {"module": "demo.engine"}},
        "systems": {"default": {"module": "demo.system"}},
        "backends": {"default": {"module": "demo.backend"}},
        "simulate": {
            "main": {
                "times": [0.0, 2.0],
                "params": {"beta": 2.0},
            }
        },
    })

    patched = configuration.patch(patch, conflict=PatchConflictMode.MERGE)

    simulate = patched.simulate["main"]
    assert simulate.engine == "default"
    assert simulate.params == {"alpha": 1.0, "beta": 2.0}


def test_configuration_model_patch_error_collects_all_duplicate_entries() -> None:
    """Error mode should report all duplicate section keys in one failure."""
    configuration = ConfigurationModel.model_validate({
        "process": {"main": {"module": "flepimop2.process.shell"}},
        "parameters": {"pi": math.pi, "r0": 0.1},
    })
    patch = ConfigurationModel.model_validate({
        "process": {"main": {"module": "flepimop2.process.shell"}},
        "parameters": {"gamma": 0.2, "pi": 3.0, "r0": 0.3},
    })

    with pytest.raises(
        ValueError,
        match="Cannot patch configuration under conflict='error'",
    ) as excinfo:
        configuration.patch(patch, conflict=PatchConflictMode.ERROR)

    message = str(excinfo.value)
    assert "process=['main']" in message
    assert "parameters=['pi', 'r0']" in message


def test_configuration_model_patch_name_prefers_other_when_both_are_set() -> None:
    """When both names are set, the patch name should win."""
    configuration = ConfigurationModel.model_validate({"name": "base"})
    patch = ConfigurationModel.model_validate({"name": "override"})

    patched = configuration.patch(patch, conflict=PatchConflictMode.MERGE)

    assert patched.name == "override"


def test_configuration_model_patch_name_uses_only_set_name() -> None:
    """When only one name is set, the patched config should keep that name."""
    configuration = ConfigurationModel.model_validate({"name": "base"})
    patch = ConfigurationModel.model_validate({})

    patched = configuration.patch(patch, conflict=PatchConflictMode.MERGE)

    assert patched.name == "base"


def test_configuration_model_patch_name_uses_patch_name_when_only_it_is_set() -> None:
    """When only the patch sets a name, the patched config should use it."""
    configuration = ConfigurationModel.model_validate({})
    patch = ConfigurationModel.model_validate({"name": "override"})

    patched = configuration.patch(patch, conflict=PatchConflictMode.MERGE)

    assert patched.name == "override"


def test_configuration_model_patch_omits_name_when_neither_is_set() -> None:
    """When neither config sets a name, the patched config should omit it too."""
    configuration = ConfigurationModel.model_validate({})
    patch = ConfigurationModel.model_validate({})

    patched = configuration.patch(patch, conflict=PatchConflictMode.MERGE)

    assert patched.name is None
    assert "name" not in patched.model_fields_set


def test_configuration_model_patch_preserves_document_start_marker() -> None:
    """Patched configs should keep `---` if either source config had it."""
    configuration = ConfigurationModel.safe_load(
        """
parameters:
  alpha: fixed(1.0)
""".lstrip()
    )
    patch = ConfigurationModel.safe_load(
        """
---
parameters:
  beta: fixed(2.0)
""".lstrip()
    )

    patched = configuration.patch(patch, conflict=PatchConflictMode.MERGE)

    assert patched.safe_dump().startswith("---\n")
