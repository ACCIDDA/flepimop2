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
"""The default project pattern, scaffolded from the bundled template."""

__all__ = ["DefaultPattern"]

from pathlib import Path

from flepimop2.pattern.abc import PatternABC

_TEMPLATE_DIR = Path(__file__).parents[2] / "templates" / "skeleton"


class DefaultPattern(PatternABC, module="default"):
    """Scaffold a fresh project from the bundled template tree."""

    def _scaffold(self, destination: Path, *, dry_run: bool = False) -> None:
        """
        Copy the bundled template tree into `destination`.

        Args:
            destination: Directory in which to create the project.
            dry_run: If `True`, perform no filesystem writes.
        """
        if dry_run:
            return
        destination.mkdir(parents=True, exist_ok=True)
        self._copy_template_tree(_TEMPLATE_DIR, destination)
