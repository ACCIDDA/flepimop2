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

from flepimop2.cli._job_command import job_group
from flepimop2.cli._simulate_command import SimulateCommand
from flepimop2.job.abc import JobDryRun, JobHandle


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
