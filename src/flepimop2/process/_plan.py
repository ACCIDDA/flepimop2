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
"""Scheduler-independent process plan types."""

__all__ = ["PlannedStep", "ProcessPlan"]

from typing import TypedDict


class PlannedStep(TypedDict):
    """Specification of a single planned process step for job execution.

    Attributes:
        command: Command-line tokens for executing the individual step.
        depends: Names of sibling process steps this step directly depends on.
    """

    command: list[str]
    depends: list[str]


ProcessPlan = dict[str, PlannedStep]
"""A dependency-aware plan mapping process-step names to planned execution steps."""
