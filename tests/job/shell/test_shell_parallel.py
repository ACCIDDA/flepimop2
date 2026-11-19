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
"""Tests for dependency-aware parallel execution in ``ShellJob``."""

import os
import signal
import subprocess  # noqa: S404
import sys
from contextlib import suppress
from pathlib import Path
from time import monotonic, sleep
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest
from pydantic import ValidationError

from flepimop2.exceptions import Flepimop2ValidationError
from flepimop2.job.abc import JobDryRun, JobHandle
from flepimop2.job.shell import ShellJob
from flepimop2.job.shell._runner import _ShellPlanRunner, _stop_process_groups
from flepimop2.process._plan import ProcessPlan

pytestmark = pytest.mark.skipif(
    os.name != "posix", reason="Parallel ShellJob currently requires POSIX"
)

_EXE = "/usr/local/bin/flepimop2"


def _parallel_job(**config: Any) -> ShellJob:
    """Create a ready-to-submit parallel backend without PATH lookups.

    Returns:
        A configured ShellJob with a cached executable.
    """
    job = ShellJob.model_validate({"execution": "parallel", **config})
    job._exe = _EXE
    return job


def _plan() -> ProcessPlan:
    """Make a diamond-shaped process DAG: independent a/b, then c.

    Returns:
        A three-step dependency-aware process plan.
    """
    return {
        "a": {
            "command": ["flepimop2", "process", "--target", "a", "--no-deps"],
            "depends": [],
        },
        "b": {
            "command": ["flepimop2", "process", "--target", "b", "--no-deps"],
            "depends": [],
        },
        "c": {
            "command": ["flepimop2", "process", "--target", "c", "--no-deps"],
            "depends": ["a", "b"],
        },
    }


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        ({}, True),
        ({"execution": "serial"}, True),
        ({"execution": "serial", "detach": False}, False),
        ({"execution": "serial", "detach": True}, True),
        ({"execution": "parallel"}, False),
        ({"execution": "parallel", "detach": False}, False),
    ],
)
def test_execution_mode_resolves_detach(
    config: dict[str, Any], *, expected: bool
) -> None:
    """Serial keeps its existing default; parallel becomes blocking."""
    job = ShellJob.model_validate(config)
    assert job.detach is expected
    assert job.model_dump()["detach"] is expected


def test_parallel_rejects_explicit_detach_true() -> None:
    """An explicit incompatible configuration fails at model validation."""
    with pytest.raises(ValidationError, match="requires detach=False"):
        ShellJob.model_validate({"execution": "parallel", "detach": True})


@pytest.mark.parametrize("workers", [0, -1])
def test_parallel_rejects_nonpositive_workers(workers: int) -> None:
    """The concurrency limit must be at least one."""
    with pytest.raises(ValidationError, match="max_workers"):
        ShellJob.model_validate({"execution": "parallel", "max_workers": workers})


def test_parallel_defaults_to_four_workers() -> None:
    """The configured concurrency limit defaults to four."""
    assert ShellJob(execution="parallel").max_workers == 4


def test_parallel_rejects_detach_mutated_after_validation() -> None:
    """The defensive runtime check protects mutated model instances."""
    job = _parallel_job()
    job.detach = True
    with (
        patch("flepimop2.job.shell._runner.subprocess.Popen") as popen,
        pytest.raises(ValueError, match="requires detach=False"),
    ):
        job.submit_plan(_plan())
    popen.assert_not_called()


def test_parallel_rejects_non_posix_platform() -> None:
    """Parallel subprocess scheduling is explicitly limited to POSIX."""
    job = _parallel_job()
    with (
        patch("flepimop2.job.shell.os", SimpleNamespace(name="nt")),
        pytest.raises(NotImplementedError, match="POSIX"),
    ):
        job.submit_plan(_plan())


def test_parallel_dry_run_lists_commands_without_starting_processes(
    tmp_path: Path,
) -> None:
    """Dry run reports all steps in dependency order and spawns nothing."""
    job = _parallel_job(max_workers=2, cwd=tmp_path)
    with (
        patch("flepimop2.job.shell._runner.subprocess.Popen") as popen,
        patch("flepimop2.job.shell.subprocess.run") as run,
    ):
        result = job.submit_plan(_plan(), dry_run=True)
    assert isinstance(result, JobDryRun)
    assert [line.split(":", 1)[0] for line in result.command.splitlines()] == [
        "a",
        "b",
        "c",
    ]
    assert f"{_EXE} process --target a --no-deps" in result.command
    assert result.details == {
        "mode": "parallel",
        "max_workers": "2",
        "cwd": str(tmp_path),
    }
    popen.assert_not_called()
    run.assert_not_called()


def test_parallel_empty_plan_returns_empty_handles() -> None:
    """An empty plan requires no subprocesses."""
    job = _parallel_job()
    with patch("flepimop2.job.shell._runner.subprocess.Popen") as popen:
        assert job.submit_plan({}) == {}
    popen.assert_not_called()


@pytest.mark.parametrize(
    "invalid_plan",
    [
        {"a": {"command": ["flepimop2", "process"], "depends": ["missing"]}},
        {"a": {"command": ["flepimop2", "process"], "depends": ["a"]}},
        {
            "a": {"command": ["flepimop2", "process"], "depends": ["b"]},
            "b": {"command": ["flepimop2", "process"], "depends": ["a"]},
        },
    ],
    ids=["missing-dependency", "self-dependency", "cycle"],
)
def test_parallel_invalid_dependencies_do_not_launch(
    invalid_plan: ProcessPlan,
) -> None:
    """Reject an invalid dependency graph before starting any work."""
    job = _parallel_job()
    with (
        patch("flepimop2.job.shell._runner.subprocess.Popen") as popen,
        pytest.raises(Flepimop2ValidationError),
    ):
        job.submit_plan(invalid_plan)
    popen.assert_not_called()


@pytest.mark.parametrize(
    "command",
    [[], ["flepimop2"], ["python", "process", "--target", "a"]],
)
def test_parallel_invalid_step_commands_do_not_launch(command: list[str]) -> None:
    """Reject malformed or unexpected executables during preflight."""
    job = _parallel_job()
    plan: ProcessPlan = {"a": {"command": command, "depends": []}}
    with (
        patch("flepimop2.job.shell._runner.subprocess.Popen") as popen,
        pytest.raises(ValueError, match="Invalid flepimop2 command"),
    ):
        job.submit_plan(plan)
    popen.assert_not_called()


def test_parallel_missing_executable_fails_before_launch() -> None:
    """The inherited submit preflight validates that the CLI exists."""
    job = ShellJob(execution="parallel")
    with (
        patch("flepimop2.job.shell.shutil.which", return_value=None),
        patch("flepimop2.job.shell._runner.subprocess.Popen") as popen,
        pytest.raises(Flepimop2ValidationError),
    ):
        job.submit_plan(_plan())
    popen.assert_not_called()


def test_parallel_reuses_cached_executable() -> None:
    """An already-resolved executable should not trigger another PATH search."""
    job = _parallel_job()
    with patch("flepimop2.job.shell.shutil.which") as which:
        job.submit_plan(_plan(), dry_run=True)
    which.assert_not_called()


def test_parallel_launches_ready_steps_with_cwd_env_and_new_session(
    tmp_path: Path,
) -> None:
    """Only initially ready branches launch, with configured Popen options."""
    job = _parallel_job(max_workers=2, cwd=tmp_path, env={"FLAG": "1"})
    pending = {step: [_EXE, *spec["command"][1:]] for step, spec in _plan().items()}
    runner = _ShellPlanRunner(
        _plan(), pending, max_workers=job.max_workers, cwd=job.cwd, env=job.env
    )
    with patch("flepimop2.job.shell._runner.subprocess.Popen") as popen:
        launched = runner._launch_ready()
    assert launched is True
    assert set(runner._running) == {"a", "b"}
    assert set(runner._pending) == {"c"}
    assert popen.call_count == 2
    for expected in ("a", "b"):
        args, kwargs = popen.call_args_list[["a", "b"].index(expected)]
        assert args[0] == [_EXE, "process", "--target", expected, "--no-deps"]
        assert kwargs == {
            "cwd": tmp_path,
            "env": {"FLAG": "1"},
            "start_new_session": True,
        }


def test_parallel_waits_for_all_dependencies_and_returns_handles() -> None:
    """A join step launches after both upstream processes exit successfully."""
    job = _parallel_job(max_workers=2)
    proc_a = MagicMock(pid=101)
    proc_b = MagicMock(pid=102)
    proc_c = MagicMock(pid=103)
    proc_a.poll.side_effect = [None, 0]
    proc_b.poll.side_effect = [None, 0]
    proc_c.poll.side_effect = [None, 0]
    launched: list[str] = []

    def spawn(argv: list[str], **_kwargs: object) -> MagicMock:
        """Record that the join cannot start until both parents were polled.

        Returns:
            The mocked subprocess for the requested step.
        """
        step = argv[argv.index("--target") + 1]
        if step == "c":
            assert proc_a.poll.call_count == 2
            assert proc_b.poll.call_count == 2
        launched.append(step)
        return {"a": proc_a, "b": proc_b, "c": proc_c}[step]

    with (
        patch("flepimop2.job.shell._runner.subprocess.Popen", side_effect=spawn),
        patch("flepimop2.job.shell._runner.sleep") as sleep,
    ):
        result = job.submit_plan(_plan())
    assert launched == ["a", "b", "c"]
    assert isinstance(result, dict)
    assert list(result) == ["a", "b", "c"]
    for step, pid in (("a", 101), ("b", 102), ("c", 103)):
        handle = result[step]
        assert isinstance(handle, JobHandle)
        assert handle.job_id == str(pid)
        assert handle.backend == "shell"
        assert handle.metadata == {"mode": "blocking", "returncode": 0, "step": step}
    assert sleep.call_count >= 1


def test_parallel_max_workers_caps_concurrent_subprocesses() -> None:
    """Scheduler never starts more subprocesses than configured workers."""
    job = _parallel_job(max_workers=2)
    plan: ProcessPlan = {
        name: {"command": ["flepimop2", "process", "--target", name], "depends": []}
        for name in ("a", "b", "c", "d", "e")
    }
    active: set[int] = set()
    peak = 0
    spawned = 0

    def spawn(_argv: list[str], **_kwargs: object) -> MagicMock:
        """Track active jobs until polling reaps each fake subprocess.

        Returns:
            A mocked subprocess that completes when polled.
        """
        nonlocal peak, spawned
        spawned += 1
        pid = 1000 + spawned
        active.add(pid)
        peak = max(peak, len(active))
        proc = MagicMock(pid=pid)

        def poll() -> int:
            """Complete this fake process when the scheduler polls it.

            Returns:
                Zero to indicate successful completion.
            """
            active.remove(pid)
            return 0

        proc.poll.side_effect = poll
        return proc

    with patch("flepimop2.job.shell._runner.subprocess.Popen", side_effect=spawn):
        handles = job.submit_plan(plan)
    assert isinstance(handles, dict)
    assert len(handles) == 5
    assert spawned == 5
    assert peak == 2
    assert not active


def test_parallel_failure_prevents_downstream_and_cleans_up() -> None:
    """A failed branch blocks the join step and cleans up the running set."""
    job = _parallel_job(max_workers=2)
    failed = MagicMock(pid=301)
    sibling = MagicMock(pid=302)
    failed.poll.return_value = 7
    sibling.poll.return_value = None
    with (
        patch(
            "flepimop2.job.shell._runner.subprocess.Popen",
            side_effect=[failed, sibling],
        ) as popen,
        patch("flepimop2.job.shell._runner._stop_process_groups") as stop,
        pytest.raises(RuntimeError, match="'a' failed with exit code 7"),
    ):
        job.submit_plan(_plan())
    assert popen.call_count == 2  # dependent step c never started
    stop.assert_called_once()
    assert set(stop.call_args.args[0]) == {"a", "b"}


def test_parallel_spawn_error_cleans_up_already_started_processes() -> None:
    """An error launching a later branch still cleans up earlier branches."""
    job = _parallel_job()
    started = MagicMock(pid=401)
    with (
        patch(
            "flepimop2.job.shell._runner.subprocess.Popen",
            side_effect=[started, OSError("spawn failed")],
        ),
        patch("flepimop2.job.shell._runner._stop_process_groups") as stop,
        pytest.raises(OSError, match="spawn failed"),
    ):
        job.submit_plan(_plan())
    stop.assert_called_once()
    assert set(stop.call_args.args[0]) == {"a"}


def test_parallel_interrupt_cleans_up_active_processes() -> None:
    """KeyboardInterrupt is handled by the BaseException cleanup path."""
    job = _parallel_job(max_workers=1)
    proc = MagicMock(pid=501)
    proc.poll.side_effect = KeyboardInterrupt
    with (
        patch("flepimop2.job.shell._runner.subprocess.Popen", return_value=proc),
        patch("flepimop2.job.shell._runner._stop_process_groups") as stop,
        pytest.raises(KeyboardInterrupt),
    ):
        job.submit_plan(_plan())
    stop.assert_called_once()
    assert set(stop.call_args.args[0]) == {"a"}


def test_stop_process_groups_sends_signals_and_reaps() -> None:
    """Cleanup sends TERM/KILL and waits for each process with bounded waits."""
    proc = MagicMock(pid=601)
    proc.wait.side_effect = [subprocess.TimeoutExpired("test", 3), 0]
    running: dict[str, Any] = {"a": proc}
    with patch("flepimop2.job.shell._runner.os.killpg") as killpg:
        _stop_process_groups(running)
    assert killpg.call_args_list == [
        call(601, signal.SIGTERM),
        call(601, signal.SIGKILL),
    ]
    assert proc.wait.call_count == 2
    assert all(c.kwargs["timeout"] >= 0 for c in proc.wait.call_args_list)


def test_stop_process_groups_ignores_already_gone_groups() -> None:
    """A process group disappearing before signaling is not fatal."""
    proc = MagicMock(pid=602)
    running: dict[str, Any] = {"a": proc}
    with patch("flepimop2.job.shell._runner.os.killpg", side_effect=ProcessLookupError):
        _stop_process_groups(running)
    assert proc.wait.call_count == 2


def test_parallel_real_subprocesses_overlap_and_join(tmp_path: Path) -> None:
    """Integration: two branches must both start before either can finish."""
    job = _parallel_job(max_workers=2)
    job._exe = sys.executable
    start_a, start_b = tmp_path / "a.started", tmp_path / "b.started"
    done_a, done_b, done_c = (
        tmp_path / "a.done",
        tmp_path / "b.done",
        tmp_path / "c.done",
    )
    branch_script = """
import pathlib
import sys
import time
start, peer, done = (pathlib.Path(x) for x in sys.argv[1:4])
start.write_text('started')
deadline = time.monotonic() + 5
while not peer.exists():
    if time.monotonic() >= deadline:
        sys.exit(13)
    time.sleep(0.01)
done.write_text('finished')
"""
    join_script = """
import pathlib
import sys
parent_a, parent_b, output = (pathlib.Path(x) for x in sys.argv[1:4])
if not (parent_a.exists() and parent_b.exists()):
    sys.exit(17)
output.write_text('finished')
"""
    plan: ProcessPlan = {
        "a": {
            "command": [
                "flepimop2",
                "-c",
                branch_script,
                str(start_a),
                str(start_b),
                str(done_a),
            ],
            "depends": [],
        },
        "b": {
            "command": [
                "flepimop2",
                "-c",
                branch_script,
                str(start_b),
                str(start_a),
                str(done_b),
            ],
            "depends": [],
        },
        "c": {
            "command": [
                "flepimop2",
                "-c",
                join_script,
                str(done_a),
                str(done_b),
                str(done_c),
            ],
            "depends": ["a", "b"],
        },
    }
    handles = job.submit_plan(plan)
    assert isinstance(handles, dict)
    assert set(handles) == {"a", "b", "c"}
    assert all(h.metadata["returncode"] == 0 for h in handles.values())
    assert done_a.is_file()
    assert done_b.is_file()
    assert done_c.is_file()


@pytest.mark.parametrize("error", [None, RuntimeError, KeyboardInterrupt, SystemExit])
def test_parallel_restores_sigterm_handler(error: type[BaseException] | None) -> None:
    """Restore the caller's handler after completion or any exception."""
    job = _parallel_job()
    proc = MagicMock(pid=701)
    proc.poll.return_value = 0
    if error is not None:
        proc.poll.side_effect = error
    previous = signal.signal(signal.SIGTERM, signal.SIG_IGN)
    try:
        with (
            patch("flepimop2.job.shell._runner.subprocess.Popen", return_value=proc),
            patch("flepimop2.job.shell._runner._stop_process_groups"),
        ):
            if error is None:
                job.submit_plan(_plan())
            else:
                with pytest.raises(error):
                    job.submit_plan(_plan())
        assert signal.getsignal(signal.SIGTERM) == signal.SIG_IGN
    finally:
        signal.signal(signal.SIGTERM, previous)


def test_parallel_sigterm_cleans_up_real_process_group(tmp_path: Path) -> None:
    """A real SIGTERM stops workers and descendants and restores the handler."""
    child = tmp_path / "child.py"
    child.write_text("""
import os
import signal
import sys
import time
from pathlib import Path

def terminate(signum, frame):
    Path('child.stopped').touch()
    sys.exit(0)

signal.signal(signal.SIGTERM, terminate)
Path('child.pid').write_text(str(os.getpid()))
time.sleep(30)
Path('unexpected.output').touch()
""")
    worker = tmp_path / "worker.py"
    worker.write_text("""
import os
import signal
import subprocess
import sys
from pathlib import Path

child = subprocess.Popen([sys.executable, 'child.py'])
def terminate(signum, frame):
    child.wait(timeout=5)
    sys.exit(0)

signal.signal(signal.SIGTERM, terminate)
Path('worker.pid').write_text(str(os.getpid()))
child.wait()
""")
    scheduler = tmp_path / "scheduler.py"
    scheduler.write_text("""
import signal
import sys
from pathlib import Path
from flepimop2.job.shell import ShellJob

job = ShellJob(execution='parallel', max_workers=1)
job._exe = sys.executable
previous = signal.getsignal(signal.SIGTERM)
try:
    job.submit_plan({
        'worker': {'command': ['flepimop2', 'worker.py'], 'depends': []},
        'downstream': {
            'command': ['flepimop2', '-c', "open('downstream.output', 'w').close()"],
            'depends': ['worker'],
        },
    })
finally:
    assert signal.getsignal(signal.SIGTERM) == previous
    Path('handler.restored').touch()
""")
    with subprocess.Popen(  # noqa: S603
        [sys.executable, str(scheduler)],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as proc:
        try:
            deadline = monotonic() + 10
            while not all(
                (tmp_path / name).exists() for name in ("worker.pid", "child.pid")
            ):
                assert proc.poll() is None, proc.communicate()
                assert monotonic() < deadline, "Workers did not start"
                sleep(0.01)
            worker_pid = int((tmp_path / "worker.pid").read_text())
            proc.send_signal(signal.SIGTERM)
            stdout, stderr = proc.communicate(timeout=10)
            assert proc.returncode == 128 + signal.SIGTERM, (stdout, stderr)
            assert (tmp_path / "child.stopped").exists()
            assert (tmp_path / "handler.restored").exists()
            assert not (tmp_path / "unexpected.output").exists()
            assert not (tmp_path / "downstream.output").exists()
            with pytest.raises(ProcessLookupError):
                os.killpg(worker_pid, 0)
        finally:
            # Also clean up if the regression leaves detached workers behind.
            worker_pid_file = tmp_path / "worker.pid"
            if worker_pid_file.exists():
                with suppress(ProcessLookupError):
                    os.killpg(int(worker_pid_file.read_text()), signal.SIGKILL)
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=5)


@pytest.mark.parametrize("signum", [signal.SIGTERM, signal.SIGINT])
@pytest.mark.parametrize("launch_point", ["execute_child", "popen"])
def test_parallel_launch_cancellation_tracks_real_worker(
    tmp_path: Path, signum: int, launch_point: str
) -> None:
    """Cancellation inside Popen or before registration cannot orphan a worker."""
    scheduler = tmp_path / "scheduler.py"
    scheduler.write_text("""
import os
import signal
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch
from flepimop2.job.shell import ShellJob

signum = int(sys.argv[1])
launch_point = sys.argv[2]
previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
original_popen = subprocess.Popen
original_execute_child = subprocess.Popen._execute_child

def cancel(proc):
    Path('worker.pid').write_text(str(proc.pid))
    os.kill(os.getpid(), signum)
    # Cancellation must still be deferred inside Popen's constructor.
    Path('launch.continued').touch()

def execute_child(self, *args, **kwargs):
    original_execute_child(self, *args, **kwargs)
    cancel(self)

def popen(*args, **kwargs):
    proc = original_popen(*args, **kwargs)
    cancel(proc)
    return proc

job = ShellJob(execution='parallel')
job._exe = sys.executable
if launch_point == 'execute_child':
    patched = patch.object(original_popen, '_execute_child', execute_child)
else:
    patched = patch('flepimop2.job.shell._runner.subprocess.Popen', popen)
with patched:
    try:
        job.submit_plan({
            'worker': {
                'command': ['flepimop2', '-c', 'import time; time.sleep(30)'],
                'depends': [],
            },
            'downstream': {
                'command': [
                    'flepimop2', '-c', "open('downstream.output', 'w').close()"
                ],
                'depends': ['worker'],
            },
        })
    except BaseException as exc:
        if signum == signal.SIGTERM:
            assert isinstance(exc, SystemExit), repr(exc)
            assert exc.code == 128 + signum
        else:
            assert isinstance(exc, KeyboardInterrupt), repr(exc)
    else:
        raise AssertionError('Cancellation was lost')
assert all(signal.getsignal(sig) == handler for sig, handler in previous.items())
Path('handler.restored').touch()
""")
    with subprocess.Popen(  # noqa: S603
        [sys.executable, str(scheduler), str(signum), launch_point],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as proc:
        try:
            stdout, stderr = proc.communicate(timeout=10)
            assert proc.returncode == 0, (stdout, stderr)
            assert (tmp_path / "launch.continued").exists()
            assert (tmp_path / "handler.restored").exists()
            assert not (tmp_path / "downstream.output").exists()
            worker_pid = int((tmp_path / "worker.pid").read_text())
            with pytest.raises(ProcessLookupError):
                os.killpg(worker_pid, 0)
        finally:
            worker_pid_file = tmp_path / "worker.pid"
            if worker_pid_file.exists():
                with suppress(ProcessLookupError):
                    os.killpg(int(worker_pid_file.read_text()), signal.SIGKILL)
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=5)
