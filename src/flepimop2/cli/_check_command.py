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
"""Check command implementation."""

__all__ = []

from pathlib import Path

from flepimop2.check import check_configuration
from flepimop2.cli._cli_command import CliCommand
from flepimop2.typing import ExitCode


class CheckCommand(CliCommand):
    """
    Validate a whole configuration without running it.

    Builds every simulate target, resolves every requested parameter, and runs
    each process step's validation hook, then reports all issues found. Exits
    with a configuration error when any issue is found.
    """

    def run(  # type: ignore[override]
        self,
        *,
        config: Path,
    ) -> ExitCode:
        """
        Execute the configuration check.

        Args:
            config: Path to the configuration file.

        Returns:
            An exit code indicating whether the configuration passed.
        """
        issues = check_configuration(config)
        if not issues:
            self.info("%s: no issues found.", config)
            return ExitCode.OKAY
        self.error("%s: %u issue(s) found.", config, len(issues))
        for issue in issues:
            context = ", ".join(f"{k}={v}" for k, v in (issue.ctx or {}).items())
            self.error(
                "[%s] %s%s", issue.kind, issue.msg, f" ({context})" if context else ""
            )
        return ExitCode.CONFIGURATION
