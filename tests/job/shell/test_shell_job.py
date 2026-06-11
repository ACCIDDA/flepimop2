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
"""Tests for `flepimop2.job.shell.ShellJob`."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue
from flepimop2.job.abc import JobDryRun, JobHandle, JobStatus
from flepimop2.job.shell import ShellJob
from flepimop2.typing import ExitCode

_EXE = "/usr/local/bin/flepimop2"


def _make_command(argv: list[str]) -> MagicMock:
    """Return a mock CliCommand whose to_argv() and command_name() are set."""
    cmd = MagicMock()
    cmd.command_name.return_value = "simulate"
    cmd.to_argv.return_value = argv
    return cmd


def test_submit_detached_returns_single_handle() -> None:
    """Submit in detached mode should return a single JobHandle."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell", "detach": True})
    cmd = _make_command(["--dry-run", "config.yaml"])

    mock_proc = MagicMock()
    mock_proc.pid = 12345

    with (
        patch("flepimop2.job.shell.shutil.which", return_value=_EXE),
        patch("flepimop2.job.shell.subprocess.Popen", return_value=mock_proc),
    ):
        handles = job.submit(cmd)

    assert isinstance(handles, JobHandle)


def test_submit_detached_uses_pid_as_job_id() -> None:
    """In detached mode, job_id should be the subprocess PID as a string."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell", "detach": True})
    cmd = _make_command([])

    mock_proc = MagicMock()
    mock_proc.pid = 99999

    with (
        patch("flepimop2.job.shell.shutil.which", return_value=_EXE),
        patch("flepimop2.job.shell.subprocess.Popen", return_value=mock_proc),
    ):
        handles = job.submit(cmd)

    assert isinstance(handles, JobHandle)
    assert handles.job_id == "99999"
    assert handles.backend == "shell"


def test_submit_detached_builds_correct_argv() -> None:
    """Popen should be called with [exe, command_name, *to_argv()]."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell", "detach": True})
    cmd = _make_command(["--dry-run", "config.yaml"])

    mock_proc = MagicMock()
    mock_proc.pid = 1

    with (
        patch("flepimop2.job.shell.shutil.which", return_value=_EXE),
        patch(
            "flepimop2.job.shell.subprocess.Popen", return_value=mock_proc
        ) as mock_popen,
    ):
        job.submit(cmd)

    called_argv = mock_popen.call_args[0][0]
    assert called_argv == [_EXE, "simulate", "--dry-run", "config.yaml"]


def test_submit_raises_when_exe_not_found() -> None:
    """Submit should raise Flepimop2ValidationError when flepimop2 is not on PATH."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell", "detach": True})
    cmd = _make_command([])

    with (
        patch("flepimop2.job.shell.shutil.which", return_value=None),
        pytest.raises(Flepimop2ValidationError),
    ):
        job.submit(cmd)


def test_submit_validate_returns_empty_list_when_exe_found() -> None:
    """_submit_validate should return [] and cache the exe when found."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell"})
    with patch("flepimop2.job.shell.shutil.which", return_value=_EXE):
        result = job._submit_validate()
    assert result == []
    assert job._exe == _EXE


def test_submit_validate_returns_issue_when_exe_missing() -> None:
    """_submit_validate should return a ValidationIssue when exe not found."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell"})
    with patch("flepimop2.job.shell.shutil.which", return_value=None):
        result = job._submit_validate()
    assert result
    assert isinstance(result[0], ValidationIssue)
    assert job._exe is None


def test_submit_dry_run_returns_dry_run() -> None:
    """submit(dry_run=True) should validate and describe, but not submit."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell"})
    cmd = _make_command([])

    with (
        patch("flepimop2.job.shell.shutil.which", return_value=_EXE),
        patch("flepimop2.job.shell.subprocess.Popen") as mock_popen,
    ):
        result = job.submit(cmd, dry_run=True)

    assert isinstance(result, JobDryRun)
    mock_popen.assert_not_called()


def test_submit_dry_run_describes_command() -> None:
    """A dry run performs preflight work and reports the command it would run."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell"})
    cmd = _make_command(["config.yaml"])

    with (
        patch("flepimop2.job.shell.shutil.which", return_value=_EXE) as mock_which,
        patch("flepimop2.job.shell.subprocess.Popen") as mock_popen,
        patch("flepimop2.job.shell.subprocess.run") as mock_run,
    ):
        result = job.submit(cmd, dry_run=True)

    assert isinstance(result, JobDryRun)
    # The argv is assembled from the resolved executable and the command...
    mock_which.assert_called()
    cmd.to_argv.assert_called()
    assert result.command == f"{_EXE} simulate config.yaml"
    assert result.details["mode"] == "detached"
    # ...but nothing is actually launched.
    mock_popen.assert_not_called()
    mock_run.assert_not_called()


def test_submit_reuses_cached_exe() -> None:
    """Submit should not call shutil.which again when _exe is already set."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell", "detach": True})
    job._exe = _EXE
    cmd = _make_command([])

    mock_proc = MagicMock()
    mock_proc.pid = 1

    with (
        patch("flepimop2.job.shell.shutil.which") as mock_which,
        patch("flepimop2.job.shell.subprocess.Popen", return_value=mock_proc),
    ):
        job.submit(cmd)

    mock_which.assert_not_called()


def test_submit_detached_starts_new_session() -> None:
    """Popen must be called with start_new_session=True in detach mode."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell", "detach": True})
    cmd = _make_command([])

    with (
        patch("flepimop2.job.shell.shutil.which", return_value=_EXE),
        patch(
            "flepimop2.job.shell.subprocess.Popen", return_value=MagicMock(pid=1)
        ) as mock_popen,
    ):
        job.submit(cmd)

    assert mock_popen.call_args.kwargs.get("start_new_session") is True


def test_submit_detached_passes_cwd_and_env(tmp_path: Path) -> None:
    """Cwd and env should be forwarded to Popen."""
    job = ShellJob.model_validate({
        "module": "flepimop2.job.shell",
        "detach": True,
        "cwd": str(tmp_path),
        "env": {"FLEPIMOP2_ENV": "test"},
    })
    cmd = _make_command([])

    with (
        patch("flepimop2.job.shell.shutil.which", return_value=_EXE),
        patch(
            "flepimop2.job.shell.subprocess.Popen", return_value=MagicMock(pid=1)
        ) as mock_popen,
    ):
        job.submit(cmd)

    kwargs = mock_popen.call_args.kwargs
    assert kwargs["cwd"] == tmp_path
    assert kwargs["env"] == {"FLEPIMOP2_ENV": "test"}


def test_submit_synchronous_returns_single_handle() -> None:
    """Submit in synchronous mode should also return a `JobHandle`."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell", "detach": False})
    cmd = _make_command([])

    mock_result = MagicMock()
    mock_result.returncode = 0

    with (
        patch("flepimop2.job.shell.shutil.which", return_value=_EXE),
        patch("flepimop2.job.shell.subprocess.run", return_value=mock_result),
    ):
        handles = job.submit(cmd)

    assert isinstance(handles, JobHandle)


def test_submit_synchronous_uses_returncode_as_job_id() -> None:
    """In synchronous mode, job_id should be the returncode as a string."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell", "detach": False})
    cmd = _make_command([])

    mock_result = MagicMock()
    mock_result.returncode = ExitCode.OKAY

    with (
        patch("flepimop2.job.shell.shutil.which", return_value=_EXE),
        patch("flepimop2.job.shell.subprocess.run", return_value=mock_result),
    ):
        handles = job.submit(cmd)

    assert isinstance(handles, JobHandle)
    assert handles.job_id == str(int(ExitCode.OKAY))
    assert handles.backend == "shell"


def test_submit_synchronous_does_not_use_popen() -> None:
    """Synchronous mode must use subprocess.run, not Popen."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell", "detach": False})
    cmd = _make_command([])

    mock_result = MagicMock()
    mock_result.returncode = 0

    with (
        patch("flepimop2.job.shell.shutil.which", return_value=_EXE),
        patch(
            "flepimop2.job.shell.subprocess.run", return_value=mock_result
        ) as mock_run,
        patch("flepimop2.job.shell.subprocess.Popen") as mock_popen,
    ):
        job.submit(cmd)

    mock_run.assert_called_once()
    mock_popen.assert_not_called()


def _shell_job() -> ShellJob:
    """Build a concrete ShellJob for status tests.

    Returns:
        A `ShellJob` with default settings.
    """
    return ShellJob.model_validate({"module": "flepimop2.job.shell"})


def test_status_blocking_zero_returncode_is_successful() -> None:
    """A blocking job with returncode 0 reports SUCCESSFUL."""
    handle = JobHandle(
        job_id="0",
        backend="shell",
        metadata={"mode": "blocking", "returncode": 0},
    )
    result = _shell_job().status(handle)
    assert result.status is JobStatus.SUCCESSFUL
    assert result.detail["returncode"] == 0


def test_status_blocking_nonzero_returncode_is_failed() -> None:
    """A blocking job with a nonzero returncode reports FAILED."""
    handle = JobHandle(
        job_id="1",
        backend="shell",
        metadata={"mode": "blocking", "returncode": 1},
    )
    result = _shell_job().status(handle)
    assert result.status is JobStatus.FAILED
    assert result.detail["returncode"] == 1


def test_status_detached_live_pid_is_running() -> None:
    """A detached job whose PID is alive reports RUNNING."""
    handle = JobHandle(job_id="12345", backend="shell", metadata={"mode": "detached"})
    with patch("flepimop2.job.shell.os.kill", return_value=None):
        result = _shell_job().status(handle)
    assert result.status is JobStatus.RUNNING


def test_status_detached_dead_pid_is_finished_unknown() -> None:
    """A detached job whose PID is gone reports FINISHED_UNKNOWN (exit unknown)."""
    handle = JobHandle(job_id="12345", backend="shell", metadata={"mode": "detached"})
    with patch("flepimop2.job.shell.os.kill", side_effect=ProcessLookupError):
        result = _shell_job().status(handle)
    assert result.status is JobStatus.FINISHED_UNKNOWN


def test_status_detached_foreign_pid_is_running() -> None:
    """A detached job whose PID is owned by another user reports RUNNING."""
    handle = JobHandle(job_id="12345", backend="shell", metadata={"mode": "detached"})
    with patch("flepimop2.job.shell.os.kill", side_effect=PermissionError):
        result = _shell_job().status(handle)
    assert result.status is JobStatus.RUNNING
