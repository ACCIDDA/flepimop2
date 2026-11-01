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
"""Tests for the `flepimop2 job` CLI group."""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from flepimop2.cli._job_command import (
    _dispatch_to_job,
    _validate_plan_result,
    job_group,
)
from flepimop2.cli._process_command import ProcessCommand
from flepimop2.cli._simulate_command import SimulateCommand
from flepimop2.job.abc import JobDryRun, JobHandle


def test_validate_plan_result_returns_job_handles() -> None:
    """A valid plan result is narrowed to string keys and JobHandle values."""
    handle = JobHandle(job_id="1", backend="test")

    assert _validate_plan_result({"step1": handle}) == {"step1": handle}


def test_validate_plan_result_rejects_non_string_step_name() -> None:
    """Plan results must identify steps by name."""
    with pytest.raises(TypeError, match="non-string process-step name"):
        _validate_plan_result({1: JobHandle(job_id="1", backend="test")})


def test_validate_plan_result_rejects_invalid_handle() -> None:
    """Plan results must contain JobHandle values."""
    with pytest.raises(TypeError, match="invalid handle for step 'step1'"):
        _validate_plan_result({"step1": "1"})


def test_process_dispatches_plan_to_capable_backend(
    tmp_path: Path,
) -> None:
    """A plan-capable backend receives the built process plan."""
    config_path = tmp_path / "config.yaml"
    _make_minimal_config(config_path)
    command = ProcessCommand(config=config_path, target="step1", dry_run=False)
    plan = {
        "step1": {
            "command": ["flepimop2", "process", "--target", "step1"],
            "depends": [],
        }
    }
    mock_job = MagicMock()
    mock_job.supports_plan = True
    mock_job.submit_plan.return_value = {"step1": JobHandle(job_id="1", backend="test")}

    with (
        patch("flepimop2.cli._job_command.ConfigurationModel.from_yaml") as mock_load,
        patch(
            "flepimop2.cli._job_command._get_config_target",
            return_value={"module": "test"},
        ),
        patch("flepimop2.cli._job_command.build_job", return_value=mock_job),
        patch.object(command, "build_plan", return_value=plan) as build_plan,
    ):
        mock_load.return_value.jobs = {"local": {"module": "test"}}
        with pytest.raises(SystemExit) as excinfo:
            _dispatch_to_job(command, {"job_target": "local", "no_cache": True})

    assert excinfo.value.code == 0
    build_plan.assert_called_once_with()
    mock_job.submit_plan.assert_called_once_with(plan, dry_run=False)
    mock_job.submit.assert_not_called()


def test_process_dispatch_resolves_configured_job_backend(
    tmp_path: Path,
) -> None:
    """The selected job target is loaded from the configuration module."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
jobs:
  local:
    module: shell
process:
  step1:
    module: shell
""".lstrip(),
        encoding="utf-8",
    )
    command = ProcessCommand(config=config_path, target="step1", dry_run=False)
    mock_job = MagicMock()
    mock_job.supports_plan = True
    mock_job.submit_plan.return_value = JobDryRun(command="planned")

    with (
        patch(
            "flepimop2.cli._job_command.build_job",
            return_value=mock_job,
        ) as build_job,
        patch.object(
            command,
            "build_plan",
            return_value={
                "step1": {
                    "command": ["flepimop2", "process", "--target", "step1"],
                    "depends": [],
                }
            },
        ),
        pytest.raises(SystemExit) as excinfo,
    ):
        _dispatch_to_job(
            command,
            {"job_target": "local", "no_cache": False},
        )

    assert excinfo.value.code == 0
    selected_backend = build_job.call_args.args[0]
    assert selected_backend.module == "shell"
    mock_job.submit_plan.assert_called_once_with(
        mock_job.submit_plan.call_args.args[0],
        dry_run=False,
    )


def test_process_plan_dispatch_forwards_dry_run_without_caching(
    tmp_path: Path,
    save_job_mock: MagicMock,
) -> None:
    """Plan dry runs reach the backend and do not cache a skipped submission."""
    config_path = tmp_path / "config.yaml"
    _make_minimal_config(config_path)
    command = ProcessCommand(config=config_path, target="step1", dry_run=True)
    plan = {
        "step1": {
            "command": ["flepimop2", "process", "--target", "step1"],
            "depends": [],
        }
    }
    mock_job = MagicMock()
    mock_job.supports_plan = True
    mock_job.submit_plan.return_value = JobDryRun(command="planned")

    with (
        patch("flepimop2.cli._job_command.ConfigurationModel.from_yaml") as mock_load,
        patch(
            "flepimop2.cli._job_command._get_config_target",
            return_value={"module": "test"},
        ),
        patch("flepimop2.cli._job_command.build_job", return_value=mock_job),
        patch.object(command, "build_plan", return_value=plan),
    ):
        mock_load.return_value.jobs = {"local": {"module": "test"}}
        with pytest.raises(SystemExit) as excinfo:
            _dispatch_to_job(
                command,
                {"job_target": "local", "no_cache": False},
            )

    assert excinfo.value.code == 0
    mock_job.submit_plan.assert_called_once_with(plan, dry_run=True)
    save_job_mock.assert_not_called()


def test_process_dispatches_command_to_submit_only_backend(
    tmp_path: Path,
) -> None:
    """A submit-only backend keeps using the ordinary submit path."""
    config_path = tmp_path / "config.yaml"
    _make_minimal_config(config_path)
    command = ProcessCommand(config=config_path, target="step1", dry_run=False)
    mock_job = MagicMock()
    mock_job.supports_plan = False
    mock_job.submit.return_value = JobHandle(job_id="1", backend="test")

    with (
        patch("flepimop2.cli._job_command.ConfigurationModel.from_yaml") as mock_load,
        patch(
            "flepimop2.cli._job_command._get_config_target",
            return_value={"module": "test"},
        ),
        patch("flepimop2.cli._job_command.build_job", return_value=mock_job),
    ):
        mock_load.return_value.jobs = {"local": {"module": "test"}}
        with pytest.raises(SystemExit) as excinfo:
            _dispatch_to_job(command, {"job_target": "local", "no_cache": True})

    assert excinfo.value.code == 0
    mock_job.submit.assert_called_once_with(command, dry_run=False)
    mock_job.submit_plan.assert_not_called()


@pytest.fixture(autouse=True)
def save_job_mock() -> Iterator[MagicMock]:
    """Stub out job-handle caching so dispatch tests don't touch the real cache.

    Caching is exercised separately by the `_cache` tests; here we only care
    about dispatch behavior, and the mocked job objects cannot be serialized.

    Yields:
        The mock standing in for `_cache.save_job`.
    """
    with patch("flepimop2.cli._job_command._cache.save_job") as mock:
        yield mock


def _make_minimal_config(config_path: Path, job_name: str = "local") -> None:
    """Write a minimal config YAML with one shell job entry."""
    config_path.write_text(
        f"jobs:\n  {job_name}:\n    module: shell\n    detach: false\n",
        encoding="utf-8",
    )


def test_job_simulate_dispatches_to_job_backend(tmp_path: Path) -> None:
    """Invoking `job simulate` should call job.submit(inner_command)."""
    config_path = tmp_path / "config.yaml"
    _make_minimal_config(config_path)

    mock_handle = JobHandle(
        job_id="12345",
        backend="shell",
        submitted_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
    )
    mock_job = MagicMock()
    mock_job.submit.return_value = mock_handle

    runner = CliRunner()
    with (
        patch("flepimop2.cli._job_command.build_job", return_value=mock_job),
        patch("flepimop2.cli._job_command.ConfigurationModel.from_yaml") as mock_load,
    ):
        mock_config = MagicMock()
        mock_config.jobs = {"local": {"module": "shell", "detach": False}}
        mock_load.return_value = mock_config

        result = runner.invoke(
            job_group,
            ["simulate", str(config_path)],
        )

    assert mock_job.submit.called
    assert result.exit_code == 0


def test_job_simulate_dry_run_reports_and_does_not_cache(
    tmp_path: Path, save_job_mock: MagicMock
) -> None:
    """A dry-run dispatch reports the skipped command and caches nothing."""
    config_path = tmp_path / "config.yaml"
    _make_minimal_config(config_path)

    mock_job = MagicMock()
    mock_job.submit.return_value = JobDryRun(
        command="flepimop2 simulate config.yaml --dry-run",
        details={"mode": "blocking"},
    )

    runner = CliRunner()
    with (
        patch("flepimop2.cli._job_command.build_job", return_value=mock_job),
        patch("flepimop2.cli._job_command.ConfigurationModel.from_yaml") as mock_load,
    ):
        mock_config = MagicMock()
        mock_config.jobs = {"local": {"module": "shell", "detach": False}}
        mock_load.return_value = mock_config

        result = runner.invoke(
            job_group,
            ["simulate", "-vv", "--dry-run", str(config_path)],
        )

    assert result.exit_code == 0
    _, kwargs = mock_job.submit.call_args
    assert kwargs["dry_run"] is True
    assert "would have submitted" in result.output
    assert "flepimop2 simulate config.yaml --dry-run" in result.output
    save_job_mock.assert_not_called()


def test_job_simulate_inner_command_not_executed_locally(tmp_path: Path) -> None:
    """The inner SimulateCommand.run() must NOT be called when dispatched via job."""
    config_path = tmp_path / "config.yaml"
    _make_minimal_config(config_path)

    mock_job = MagicMock()
    mock_job.submit.return_value = JobHandle(
        job_id="1",
        backend="shell",
        submitted_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
    )

    runner = CliRunner()
    with (
        patch("flepimop2.cli._job_command.build_job", return_value=mock_job),
        patch("flepimop2.cli._job_command.ConfigurationModel.from_yaml") as mock_load,
        patch("flepimop2.cli._simulate_command.SimulateCommand.run") as mock_run,
    ):
        mock_config = MagicMock()
        mock_config.jobs = {"local": {"module": "shell", "detach": False}}
        mock_load.return_value = mock_config

        runner.invoke(job_group, ["simulate", str(config_path)])

    mock_run.assert_not_called()


def test_job_simulate_passes_inner_command_to_submit(tmp_path: Path) -> None:
    """The CliCommand instance handed to submit should be a SimulateCommand."""
    config_path = tmp_path / "config.yaml"
    _make_minimal_config(config_path)

    captured: dict[str, object] = {}
    mock_handle = JobHandle(
        job_id="1",
        backend="shell",
        submitted_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
    )

    def capture_submit(cmd: object, **_kwargs: object) -> object:
        captured["cmd"] = cmd
        return mock_handle

    mock_job = MagicMock()
    mock_job.submit.side_effect = capture_submit

    runner = CliRunner()
    with (
        patch("flepimop2.cli._job_command.build_job", return_value=mock_job),
        patch("flepimop2.cli._job_command.ConfigurationModel.from_yaml") as mock_load,
    ):
        mock_config = MagicMock()
        mock_config.jobs = {"local": {"module": "shell", "detach": False}}
        mock_load.return_value = mock_config

        runner.invoke(job_group, ["simulate", str(config_path)])

    assert isinstance(captured.get("cmd"), SimulateCommand)


def test_job_simulate_submits_and_produces_handle(tmp_path: Path) -> None:
    """`flepimop2 job simulate` should call submit and receive a JobHandle."""
    config_path = tmp_path / "config.yaml"
    _make_minimal_config(config_path)

    handle = JobHandle(
        job_id="99999",
        backend="shell",
        submitted_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
    )
    mock_job = MagicMock()
    mock_job.submit.return_value = handle

    runner = CliRunner()
    with (
        patch("flepimop2.cli._job_command.build_job", return_value=mock_job),
        patch("flepimop2.cli._job_command.ConfigurationModel.from_yaml") as mock_load,
    ):
        mock_config = MagicMock()
        mock_config.jobs = {"local": {"module": "shell", "detach": False}}
        mock_load.return_value = mock_config

        result = runner.invoke(job_group, ["simulate", str(config_path)])

    assert result.exit_code == 0
    mock_job.submit.assert_called_once()
    submitted_handle = mock_job.submit.call_args[0][0]
    assert isinstance(submitted_handle, SimulateCommand)


def test_job_target_option_selects_named_job(tmp_path: Path) -> None:
    """-j / --job-target on the subcommand should resolve the named job entry."""
    config_path = tmp_path / "config.yaml"
    _make_minimal_config(config_path, job_name="cluster")

    mock_job = MagicMock()
    mock_job.submit.return_value = JobHandle(
        job_id="1",
        backend="shell",
        submitted_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
    )

    runner = CliRunner()
    with (
        patch("flepimop2.cli._job_command.build_job", return_value=mock_job),
        patch("flepimop2.cli._job_command.ConfigurationModel.from_yaml") as mock_load,
        patch("flepimop2.cli._job_command._get_config_target") as mock_target,
    ):
        mock_config = MagicMock()
        mock_config.jobs = {"cluster": {"module": "shell"}}
        mock_load.return_value = mock_config
        mock_target.return_value = mock_config.jobs["cluster"]

        runner.invoke(
            job_group,
            ["simulate", "-j", "cluster", str(config_path)],
        )

    mock_target.assert_called_once_with(mock_config.jobs, "cluster", "job")
