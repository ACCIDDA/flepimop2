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
"""Unit tests for referential, acyclic, and contract checks in flepimop2 check."""

from pathlib import Path
from typing import Any

import pytest

from flepimop2.check import _SECTION_BUILDERS, check_configuration
from flepimop2.configuration import ConfigurationModel
from flepimop2.engine.wrapper import WrapperEngine
from flepimop2.exceptions import ValidationIssue
from flepimop2.process.abc import ProcessABC
from flepimop2.process.shell import ShellProcess
from flepimop2.system.abc import SystemABC

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


def _valid_config(tmp_path: Path) -> dict[str, Any]:
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


# =============================================================================
# 1. Referential Integrity Checks
# =============================================================================


def test_referential_integrity_unknown_system_in_simulate(tmp_path: Path) -> None:
    """A simulate target referencing an unknown system is reported."""
    raw = _valid_config(tmp_path)
    raw["simulate"]["demo"]["system"] = "nonexistent_system"

    issues = check_configuration(raw)

    assert len(issues) > 0
    assert any(
        "nonexistent_system" in issue.msg or issue.kind == "configuration"
        for issue in issues
    )


def test_referential_integrity_unknown_engine_in_simulate(tmp_path: Path) -> None:
    """A simulate target referencing an unknown engine is reported."""
    raw = _valid_config(tmp_path)
    raw["simulate"]["demo"]["engine"] = "nonexistent_engine"

    issues = check_configuration(raw)

    assert len(issues) > 0
    assert any(
        "nonexistent_engine" in issue.msg or issue.kind == "configuration"
        for issue in issues
    )


def test_referential_integrity_unknown_backend_in_simulate(tmp_path: Path) -> None:
    """A simulate target referencing an unknown backend is reported."""
    raw = _valid_config(tmp_path)
    raw["simulate"]["demo"]["backend"] = "nonexistent_backend"

    issues = check_configuration(raw)

    assert len(issues) > 0
    assert any(
        "nonexistent_backend" in issue.msg or issue.kind == "configuration"
        for issue in issues
    )


def test_referential_integrity_unknown_scenario_in_simulate(tmp_path: Path) -> None:
    """A simulate target referencing an unknown scenario is reported."""
    raw = _valid_config(tmp_path)
    raw["simulate"]["demo"]["scenario"] = "nonexistent_scenario"

    issues = check_configuration(ConfigurationModel.model_validate(raw))

    scenario_issue = next(
        (
            i
            for i in issues
            if i.kind == "missing_dependency"
            and i.ctx
            and i.ctx.get("section") == "scenarios"
        ),
        None,
    )
    assert scenario_issue is not None
    assert scenario_issue.ctx is not None
    assert scenario_issue.ctx.get("dependency") == "nonexistent_scenario"


def test_referential_integrity_unknown_process_dependency(tmp_path: Path) -> None:
    """A process step depending on an unknown step is reported."""
    raw = _valid_config(tmp_path)
    raw["process"] = {
        "step_a": {
            "module": "shell",
            "command": "echo",
            "depends": ["unknown_upstream_step"],
        }
    }

    issues = check_configuration(ConfigurationModel.model_validate(raw))

    kinds = {i.kind for i in issues}
    assert "unknown_dependency" in kinds or "missing_dependency" in kinds


def test_referential_integrity_missing_required_parameter(tmp_path: Path) -> None:
    """A missing required parameter requested by the system is reported."""
    raw = _valid_config(tmp_path)
    del raw["parameters"]["beta"]

    issues = check_configuration(ConfigurationModel.model_validate(raw))

    missing = next((i for i in issues if i.kind == "missing_parameter"), None)
    assert missing is not None
    assert missing.ctx == {"target": "demo", "parameter": "beta"}


# =============================================================================
# 2. Acyclic / DAG Integrity Checks
# =============================================================================


def test_acyclic_check_process_dependency_cycle(tmp_path: Path) -> None:
    """A cycle among process dependencies is detected and reported."""
    raw = _valid_config(tmp_path)
    raw["process"] = {
        "step_1": {"module": "shell", "command": "echo", "depends": ["step_2"]},
        "step_2": {"module": "shell", "command": "echo", "depends": ["step_3"]},
        "step_3": {"module": "shell", "command": "echo", "depends": ["step_1"]},
    }

    issues = check_configuration(ConfigurationModel.model_validate(raw))

    kinds = {i.kind for i in issues}
    assert "dependency_cycle" in kinds


def test_acyclic_check_process_self_dependency(tmp_path: Path) -> None:
    """A process step that depends on itself is reported."""
    raw = _valid_config(tmp_path)
    raw["process"] = {
        "step_self": {"module": "shell", "command": "echo", "depends": ["step_self"]}
    }

    issues = check_configuration(ConfigurationModel.model_validate(raw))

    kinds = {i.kind for i in issues}
    assert "self_dependency" in kinds or "dependency_cycle" in kinds


# =============================================================================
# 3. Contract & Compatibility Checks
# =============================================================================


def test_contract_check_parameter_shape_mismatch(tmp_path: Path) -> None:
    """A parameter that samples to the wrong shape for requested axes is reported."""
    raw = _valid_config(tmp_path)
    raw["systems"]["demo"]["requested_parameters"]["gamma"] = {
        "axes": ["age"],
        "broadcast": False,
    }
    raw["parameters"]["gamma"] = {"module": "fixed", "value": 0.1}

    issues = check_configuration(ConfigurationModel.model_validate(raw))

    shape_issue = next(
        (i for i in issues if i.kind in {"parameter_shape", "parameter_resolution"}),
        None,
    )
    assert shape_issue is not None
    assert shape_issue.ctx is not None
    assert shape_issue.ctx.get("parameter") == "gamma"


def test_contract_check_engine_system_incompatibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Issues returned by engine.validate_system(system) are collected."""
    raw = _valid_config(tmp_path)

    def mock_validate_system(
        self: WrapperEngine,  # noqa: ARG001
        system: SystemABC,  # noqa: ARG001
    ) -> list[ValidationIssue]:
        return [
            ValidationIssue(
                msg="Engine is incompatible with system state transitions.",
                kind="engine_system_incompatible",
                ctx={"engine": "demo", "system": "demo"},
            )
        ]

    monkeypatch.setattr(WrapperEngine, "validate_system", mock_validate_system)

    issues = check_configuration(ConfigurationModel.model_validate(raw))

    incompat = next((i for i in issues if i.kind == "engine_system_incompatible"), None)
    assert incompat is not None
    assert "Engine is incompatible" in incompat.msg


def test_contract_check_module_validate_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A component module's validate_module() hook is executed and collected."""
    raw = _valid_config(tmp_path)
    raw["process"] = {"verify_step": {"module": "shell", "command": "echo"}}

    def mock_validate_module(self: ProcessABC) -> list[ValidationIssue]:  # noqa: ARG001
        return [
            ValidationIssue(
                msg="Binary requirements not satisfied.",
                kind="missing_binary",
                ctx={"binary": "custom_bin"},
            )
        ]

    monkeypatch.setattr(ProcessABC, "validate_module", mock_validate_module)

    issues = check_configuration(ConfigurationModel.model_validate(raw))

    binary_issue = next((i for i in issues if i.kind == "missing_binary"), None)
    assert binary_issue is not None
    assert binary_issue.ctx is not None
    assert binary_issue.ctx.get("process") == "verify_step"
    assert binary_issue.ctx.get("binary") == "custom_bin"


def _scenario_process_config() -> dict[str, Any]:
    """Build a shared process whose command comes from each scenario tuple.

    Returns:
        The scenario and process configuration.
    """
    return {
        "scenarios": {
            "first": {
                "module": "grid",
                "processes": ["shared"],
                "parameters": {"cmd": ["echo", "printf"]},
            },
            "second": {
                "module": "grid",
                "processes": ["shared"],
                "parameters": {"cmd": ["true"]},
            },
        },
        "process": {"shared": {"module": "shell", "command": "{cmd}"}},
    }


@pytest.mark.parametrize(
    ("processes", "kind"),
    [
        (["missing"], "unknown_process"),
        ("shared", "malformed_processes"),
        (["shared", "shared"], "duplicate_process"),
    ],
)
def test_scenario_process_references_are_checked(processes: object, kind: str) -> None:
    """The checker validates scenario-owned references just like the runner."""
    config = _scenario_process_config()
    config["scenarios"]["first"]["processes"] = processes

    assert kind in {issue.kind for issue in check_configuration(config)}


def test_scenario_process_duplicates_are_checked() -> None:
    """Colliding runs are reported before any process is executed."""
    config = _scenario_process_config()
    config["scenarios"]["second"]["parameters"]["cmd"] = ["echo"]

    assert "duplicate_process_run" in {
        issue.kind for issue in check_configuration(config)
    }


def test_expanded_process_configuration_is_checked() -> None:
    """A valid template can still produce an invalid module configuration."""
    config = _scenario_process_config()
    config["scenarios"]["first"]["parameters"]["cmd"] = [""]

    issues = check_configuration(config)

    assert len(issues) == 1
    assert issues[0].kind == "process_build"
    assert issues[0].ctx is not None
    assert issues[0].ctx["process"] == "shared"


def test_each_expanded_process_is_validated_without_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Shared process validation sees expanded values and never runs commands."""
    commands: list[str] = []

    def validate(self: ShellProcess) -> list[ValidationIssue]:
        commands.append(self.command)
        return []

    def execute(self: ShellProcess, *, dry_run: bool) -> None:  # noqa: ARG001
        pytest.fail("Configuration checking must not execute processes")

    monkeypatch.setattr(ShellProcess, "validate_module", validate)
    monkeypatch.setattr(ShellProcess, "_process", execute)

    assert check_configuration(_scenario_process_config()) == []
    assert commands == ["echo", "printf", "true"]


def test_process_templates_are_expanded_before_typed_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A numeric module field accepts substituted values, not raw placeholders."""
    counts: list[int] = []

    class CountingProcess(ProcessABC, module="counting"):
        n: int

        def validate_module(self) -> list[ValidationIssue]:
            counts.append(self.n)
            return []

        def _process(self, *, dry_run: bool) -> None:  # noqa: ARG002
            pytest.fail("Configuration checking must not execute processes")

    monkeypatch.setitem(
        _SECTION_BUILDERS, "process", ("process", CountingProcess.model_validate)
    )
    config = {
        "scenarios": {
            "sweep": {
                "module": "grid",
                "processes": ["count"],
                "parameters": {"n": [1, 2]},
            }
        },
        "process": {"count": {"module": "flepimop2.process.counting", "n": "{n}"}},
    }

    assert check_configuration(config) == []
    assert counts == [1, 2]


def test_process_expansion_errors_do_not_hide_unrelated_module_errors() -> None:
    """The checker keeps collecting issues after a process cannot expand."""
    config = _scenario_process_config()
    config["scenarios"]["second"]["parameters"]["cmd"] = ["echo"]
    config["engines"] = {"bad": {"module": "wrapper"}}

    issues = check_configuration(config)

    assert {"duplicate_process_run", "engine_build"} <= {issue.kind for issue in issues}
    duplicate = next(issue for issue in issues if issue.kind == "duplicate_process_run")
    assert duplicate.ctx is not None
    assert duplicate.ctx["target"] == "shared"
