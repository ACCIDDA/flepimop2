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
from flepimop2.job.abc import JobHandle
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

    assert handles is not None
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


def test_submit_dry_run_returns_none() -> None:
    """submit(dry_run=True) should validate and return None without submitting."""
    job = ShellJob.model_validate({"module": "flepimop2.job.shell"})
    cmd = _make_command([])

    with (
        patch("flepimop2.job.shell.shutil.which", return_value=_EXE),
        patch("flepimop2.job.shell.subprocess.Popen") as mock_popen,
    ):
        handles = job.submit(cmd, dry_run=True)

    assert handles is None
    mock_popen.assert_not_called()


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

    assert handles is not None
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
