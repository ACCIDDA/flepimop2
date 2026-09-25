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
"""Tests for `flepimop2 check` and `flepimop2.check.check_configuration`."""

from pathlib import Path
from typing import Any

import yaml
from click.testing import CliRunner

from flepimop2.check import check_configuration
from flepimop2.cli._cli import cli
from flepimop2.configuration import ConfigurationModel
from flepimop2.typing import ExitCode

ENGINE_SCRIPT = (
    Path(__file__).parent.parent
    / "engine"
    / "engine_wrapper_assets"
    / "dummy_engine.py"
)
SYSTEM_SCRIPT = (
    Path(__file__).parent.parent
    / "system"
    / "system_wrapper_assets"
    / "wrapper_system_with_extras.py"
)


def _config(tmp_path: Path) -> dict[str, Any]:
    output_root = tmp_path / "model_output"
    output_root.mkdir(exist_ok=True)
    return {
        "axes": {"age": {"kind": "categorical", "labels": ["0-17", "18-64", "65+"]}},
        "systems": {
            "demo": {
                "module": "wrapper",
                "script": str(SYSTEM_SCRIPT),
                "state_change": "flow",
                "requested_parameters": {
                    "beta": None,
                    "gamma": {"axes": ["age"], "broadcast": True},
                },
                "model_state": {
                    "parameter_names": ["s0", "i0", "r0"],
                    "axes": ["age"],
                    "broadcast": True,
                    "labels": ["S", "I", "R"],
                },
            }
        },
        "engines": {
            "demo": {
                "module": "wrapper",
                "script": str(ENGINE_SCRIPT),
                "state_change": "flow",
            }
        },
        "backends": {"demo": {"module": "csv", "root": str(output_root)}},
        "parameters": {
            "s0": {"module": "fixed", "value": 100.0},
            "i0": {"module": "fixed", "value": 1.0},
            "r0": {"module": "fixed", "value": 0.0},
            "beta": {"module": "fixed", "value": 0.3},
            "gamma": {"module": "fixed", "value": 0.1},
        },
        "simulate": {
            "demo": {
                "system": "demo",
                "engine": "demo",
                "backend": "demo",
                "times": [0.0, 1.0, 2.0],
            }
        },
    }


def test_valid_configuration_has_no_issues(tmp_path: Path) -> None:
    """A complete configuration passes every check."""
    assert (
        check_configuration(ConfigurationModel.model_validate(_config(tmp_path))) == []
    )


def test_missing_parameter_and_bad_process_are_all_reported(tmp_path: Path) -> None:
    """Independent problems are reported together rather than raised."""
    raw = _config(tmp_path)
    del raw["parameters"]["beta"]
    raw["process"] = {"broken": {"module": "flepimop2_nonexistent_process"}}

    issues = check_configuration(ConfigurationModel.model_validate(raw))

    kinds = {issue.kind for issue in issues}
    assert "missing_parameter" in kinds
    assert "process_build" in kinds
    missing = next(i for i in issues if i.kind == "missing_parameter")
    assert missing.ctx == {"target": "demo", "parameter": "beta"}


def test_unparseable_configuration_is_one_issue(tmp_path: Path) -> None:
    """A file that fails to parse yields a configuration issue, not a traceback."""
    path = tmp_path / "config.yaml"
    path.write_text("systems: [not, a, mapping\n", encoding="utf-8")

    issues = check_configuration(path)

    assert [issue.kind for issue in issues] == ["configuration"]


def test_check_command_exit_codes(tmp_path: Path) -> None:
    """The CLI exits cleanly when valid and with a configuration error otherwise."""
    good = tmp_path / "good.yaml"
    good.write_text(yaml.safe_dump(_config(tmp_path)), encoding="utf-8")
    bad_raw = _config(tmp_path)
    del bad_raw["parameters"]["beta"]
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(bad_raw), encoding="utf-8")

    runner = CliRunner()
    ok = runner.invoke(cli, ["check", str(good)], catch_exceptions=False)
    failed = runner.invoke(cli, ["check", str(bad)], catch_exceptions=False)

    assert ok.exit_code == ExitCode.OKAY
    assert failed.exit_code == ExitCode.CONFIGURATION
