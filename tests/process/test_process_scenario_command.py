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
"""Exercise scenario-owned process references through the process command."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from flepimop2.cli._process_command import ProcessCommand
from flepimop2.exceptions import Flepimop2ValidationError


def _write_config(tmp_path: Path, config: dict[str, Any]) -> Path:
    """Write a process configuration for a command run.

    Returns:
        Path to the configuration file.
    """
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False))
    return path


def _run_and_record(
    monkeypatch: pytest.MonkeyPatch,
    path: Path,
    *,
    force: int = 0,
    dry_run: bool = False,
) -> list[tuple[str, bool, bool]]:
    """Run a plan with a recorder in place of process module execution.

    Returns:
        Recorded commands and execution flags in their execution order.
    """
    calls: list[tuple[str, bool, bool]] = []

    class Recorder:
        def __init__(self, config: dict[str, Any]) -> None:
            self.command = config["command"]

        def execute(self, *, dry_run: bool, force: bool) -> None:
            calls.append((self.command, dry_run, force))

    monkeypatch.setattr("flepimop2.cli._process_command.build_process", Recorder)
    ProcessCommand(config=path).run(
        config=path, target="after", force=force, dry_run=dry_run
    )
    return calls


def _shared_process_config() -> dict[str, Any]:
    """Build a plan with one process used by two scenarios.

    Returns:
        The scenario and process configuration.
    """
    return {
        "scenarios": {
            "first": {
                "module": "grid",
                "processes": ["shared"],
                "parameters": {"beta": ["a", "b"]},
            },
            "unrelated": {
                "module": "grid",
                "processes": [],
                "parameters": {"beta": ["unused"]},
            },
            "second": {
                "module": "grid",
                "processes": ["shared"],
                "parameters": {"beta": ["c"]},
            },
        },
        "process": {
            "fetch": {"module": "shell", "command": "fetch"},
            "shared": {
                "module": "shell",
                "depends": ["fetch"],
                "command": "run-{beta}",
            },
            "after": {
                "module": "shell",
                "depends": ["shared"],
                "command": "after",
            },
        },
    }


def test_two_scenarios_share_one_process_and_barrier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A shared process expands in scenario order, between one fetch and after."""
    path = _write_config(tmp_path, _shared_process_config())
    assert _run_and_record(monkeypatch, path) == [
        ("fetch", False, False),
        ("run-a", False, False),
        ("run-b", False, False),
        ("run-c", False, False),
        ("after", False, False),
    ]


@pytest.mark.parametrize(
    ("force", "expected"),
    [(0, (False, False)), (1, (False, True)), (2, (True, True))],
)
def test_force_and_dry_run_reach_each_expansion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    force: int,
    expected: tuple[bool, bool],
) -> None:
    """The force counter and dry-run flag retain their plan-step meanings."""
    path = _write_config(tmp_path, _shared_process_config())
    calls = _run_and_record(monkeypatch, path, force=force, dry_run=True)
    dependency_forced, target_forced = expected
    assert calls == [
        ("fetch", True, dependency_forced),
        ("run-a", True, dependency_forced),
        ("run-b", True, dependency_forced),
        ("run-c", True, dependency_forced),
        ("after", True, target_forced),
    ]


@pytest.mark.parametrize("bad_association", ["unknown", "scalar", "legacy"])
def test_bad_associations_fail_before_dependency_executes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    bad_association: str,
) -> None:
    """No step runs when a scenario association is invalid."""
    config = _shared_process_config()
    if bad_association == "unknown":
        config["scenarios"]["second"]["processes"] = ["missing"]
    elif bad_association == "scalar":
        config["scenarios"]["second"]["processes"] = "shared"
    else:
        config["process"]["shared"]["scenario"] = "first"
    path = _write_config(tmp_path, config)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr("flepimop2.cli._process_command.build_process", calls.append)
    with pytest.raises(Flepimop2ValidationError):
        ProcessCommand(config=path).run(
            config=path, target="after", force=0, dry_run=False
        )
    assert calls == []


def test_duplicate_expanded_runs_fail_before_dependency_executes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Equal run configurations could overwrite one output, so fail early."""
    config = _shared_process_config()
    config["scenarios"]["second"]["parameters"]["beta"] = ["a"]
    path = _write_config(tmp_path, config)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr("flepimop2.cli._process_command.build_process", calls.append)
    with pytest.raises(Flepimop2ValidationError) as excinfo:
        ProcessCommand(config=path).run(
            config=path, target="after", force=0, dry_run=False
        )
    assert excinfo.value.issues[0].kind == "duplicate_process_run"
    assert calls == []
