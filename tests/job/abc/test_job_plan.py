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
"""Tests for `JobABC.submit_plan` default behavior and validation."""

from typing import TYPE_CHECKING, ClassVar

import pytest

from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue
from flepimop2.job.abc import JobABC, JobDryRun, JobHandle, JobStatusResult
from flepimop2.process.abc import ProcessPlan

if TYPE_CHECKING:
    from flepimop2.cli import CliCommand


class _DummySubmitOnlyJob(JobABC, module="dummy_submit_only"):
    """Backend without plan support."""

    def _submit(
        self,
        command: "CliCommand",  # noqa: ARG002
        *,
        dry_run: bool = False,  # noqa: ARG002
    ) -> JobHandle | JobDryRun:
        return JobHandle(job_id="1", backend=self.module)

    def _status(
        self,
        handle: JobHandle,
    ) -> JobStatusResult:
        raise NotImplementedError


class _DummyValidatingJob(JobABC, module="dummy_validating"):
    """Backend that fails validation."""

    def _submit(
        self,
        command: "CliCommand",  # noqa: ARG002
        *,
        dry_run: bool = False,  # noqa: ARG002
    ) -> JobHandle | JobDryRun:
        return JobHandle(job_id="1", backend=self.module)

    def _submit_validate(self) -> list[ValidationIssue]:
        return [ValidationIssue(msg="Backend offline.", kind="offline")]

    def _status(
        self,
        handle: JobHandle,
    ) -> JobStatusResult:
        raise NotImplementedError


class _DummyPlanCapableJob(JobABC, module="dummy_plan_capable"):
    """Backend with plan support."""

    supports_plan: ClassVar[bool] = True

    def _submit(
        self,
        command: "CliCommand",  # noqa: ARG002
        *,
        dry_run: bool = False,  # noqa: ARG002
    ) -> JobHandle | JobDryRun:
        return JobHandle(job_id="1", backend=self.module)

    def _submit_plan(
        self,
        plan: ProcessPlan,
        *,
        dry_run: bool = False,
    ) -> dict[str, JobHandle] | JobDryRun:
        if dry_run:
            return JobDryRun(command="dry-run-plan")
        return {step: JobHandle(job_id=step, backend=self.module) for step in plan}

    def _status(
        self,
        handle: JobHandle,
    ) -> JobStatusResult:
        raise NotImplementedError


def test_submit_plan_default_raises_not_implemented() -> None:
    """Submit-only backend raises NotImplementedError on submit_plan."""
    job = _DummySubmitOnlyJob()
    plan: ProcessPlan = {"step1": {"command": ["flepimop2", "process"], "depends": []}}
    with pytest.raises(
        NotImplementedError, match="does not support dependency-aware plans"
    ):
        job.submit_plan(plan)


def test_submit_plan_validates_module_before_submission() -> None:
    """Validation issues prevent plan submission."""
    job = _DummyValidatingJob()
    plan: ProcessPlan = {"step1": {"command": ["flepimop2", "process"], "depends": []}}
    with pytest.raises(Flepimop2ValidationError, match="Backend offline"):
        job.submit_plan(plan)


def test_submit_plan_delegates_to_implementation() -> None:
    """Capable backend delegates plan submission and forwards dry_run."""
    job = _DummyPlanCapableJob()
    plan: ProcessPlan = {"step1": {"command": ["flepimop2", "process"], "depends": []}}

    dry_result = job.submit_plan(plan, dry_run=True)
    assert isinstance(dry_result, JobDryRun)
    assert dry_result.command == "dry-run-plan"

    live_result = job.submit_plan(plan, dry_run=False)
    assert isinstance(live_result, dict)
    assert "step1" in live_result
    assert live_result["step1"].job_id == "step1"
