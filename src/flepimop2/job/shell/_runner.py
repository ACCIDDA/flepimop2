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
"""Private scheduler and process lifecycle helpers for shell plans."""

import os
import signal
import subprocess  # noqa: S404
from contextlib import contextmanager, suppress
from threading import current_thread, main_thread
from time import monotonic, sleep
from typing import TYPE_CHECKING

from flepimop2.job.abc import JobHandle
from flepimop2.process._plan import ProcessPlan

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path
    from types import FrameType


class _ShellPlanRunner:
    """Run a validated plan with bounded concurrency and failure cleanup.

    Each instance owns the execution state for one submission. Commands must
    already be resolved and ordered by dependency before calling ``run``.
    """

    def __init__(
        self,
        plan: ProcessPlan,
        commands: dict[str, list[str]],
        *,
        max_workers: int,
        cwd: "Path | None",
        env: dict[str, str] | None,
    ) -> None:
        """Store execution options and initialize this submission's state."""
        self._plan = plan
        self._pending = commands.copy()
        self._running: dict[str, subprocess.Popen[bytes]] = {}
        self._completed: dict[str, JobHandle] = {}
        self._step_order = list(commands)
        self._max_workers = max_workers
        self._cwd = cwd
        self._env = env

    def run(self) -> dict[str, JobHandle]:
        """Execute ready steps until every worker has completed successfully.

        Returns:
            Completed handles in the original dependency order.

        Raises:
            RuntimeError: If a step fails or remaining steps cannot progress.
        """
        with _manage_process_groups(self._running):
            while self._pending or self._running:
                progressed = self._collect_completed()
                progressed = self._launch_ready() or progressed

                if self._pending and not self._running:
                    msg = (
                        "Process plan cannot progress. Remaining steps: "
                        f"{sorted(self._pending)}"
                    )
                    raise RuntimeError(msg)

                if self._running and not progressed:
                    sleep(0.05)

        return {step: self._completed[step] for step in self._step_order}

    def _collect_completed(self) -> bool:
        """Record successful workers and fail before launching downstream steps.

        Returns:
            Whether at least one worker completed.

        Raises:
            RuntimeError: If a worker exits with a nonzero return code.
        """
        progressed = False
        for step, proc in list(self._running.items()):
            returncode = proc.poll()
            if returncode is None:
                continue
            if returncode != 0:
                msg = f"Process step '{step}' failed with exit code {returncode}."
                raise RuntimeError(msg)

            self._completed[step] = JobHandle(
                job_id=str(proc.pid),
                backend="shell",
                metadata={
                    "mode": "blocking",
                    "returncode": returncode,
                    "step": step,
                },
            )
            del self._running[step]
            progressed = True
        return progressed

    def _launch_ready(self) -> bool:
        """Fill available worker slots with steps whose prerequisites succeeded.

        Returns:
            Whether at least one worker was launched.
        """
        launched = False
        for step, argv in list(self._pending.items()):
            if len(self._running) >= self._max_workers:
                break
            if not all(dep in self._completed for dep in self._plan[step]["depends"]):
                continue

            # Track each child before cancellation can unwind its launch.
            with _defer_cancellation():
                self._running[step] = subprocess.Popen(  # noqa: S603
                    argv,
                    cwd=self._cwd,
                    env=self._env,
                    start_new_session=True,
                )
            del self._pending[step]
            launched = True
        return launched


@contextmanager
def _manage_process_groups(
    running: dict[str, subprocess.Popen[bytes]],
) -> "Generator[None]":
    """Clean up workers on failure or cancellation and restore signal handlers.

    Yields:
        Control while worker processes are being launched and monitored.
    """
    # Python signal handlers can only be installed by the main thread.
    handle_sigterm = current_thread() is main_thread()
    if handle_sigterm:
        previous_sigterm = signal.signal(signal.SIGTERM, _exit_on_sigterm)

    try:
        yield
    except BaseException:
        _stop_process_groups(running)
        raise
    finally:
        if handle_sigterm:
            signal.signal(signal.SIGTERM, previous_sigterm)


@contextmanager
def _defer_cancellation() -> "Generator[None]":
    """Defer SIGINT/SIGTERM until a newly spawned worker is tracked.

    Use handlers rather than signal masks so workers do not inherit blocked
    cancellation signals. Only the main thread can install Python handlers.

    Yields:
        Control while cancellation handlers only record incoming signals.
    """
    received: list[int] = []

    def defer(signum: int, _frame: "FrameType | None") -> None:
        """Record cancellation without interrupting process creation."""
        received.append(signum)

    previous = {}
    try:
        if current_thread() is main_thread():
            for sig in (signal.SIGINT, signal.SIGTERM):
                previous[sig] = signal.signal(sig, defer)
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        if received:
            signal.raise_signal(received[0])


def _exit_on_sigterm(signum: int, _frame: "FrameType | None") -> None:
    """Unwind plan execution while allowing process-group cleanup to finish.

    Raises:
        SystemExit: With the conventional exit status for signal cancellation.
    """
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    raise SystemExit(128 + signum)


def _stop_process_groups(
    running: dict[str, subprocess.Popen[bytes]],
) -> None:
    """Terminate and reap running subprocesses with bounded waits."""
    processes = list(running.values())

    for sig, timeout in (
        (signal.SIGTERM, 3.0),
        (signal.SIGKILL, 1.0),
    ):
        for proc in processes:
            with suppress(ProcessLookupError):
                os.killpg(proc.pid, sig)

        deadline = monotonic() + timeout

        for proc in processes:
            with suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=max(0.0, deadline - monotonic()))
