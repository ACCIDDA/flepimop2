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
"""The bundled copy pattern: scaffold a project from the template tree."""

__all__ = ["CopyPattern"]

from pathlib import Path

from flepimop2.pattern.abc import PatternABC

_TEMPLATE_DIR = Path(__file__).parents[2] / "templates" / "skeleton"


class CopyPattern(PatternABC, module="copy"):
    """Scaffold a project by copying a source tree.

    The `source` directory is copied verbatim into the target. It defaults to the
    bundled project template, so `flepimop2 pattern` with no `--source` produces
    the documented quickstart; point `source` at another project to pattern off
    it instead.
    """

    # Directory to copy from; None uses the bundled project template.
    source: Path | None = None

    def _source_dir(self) -> Path:
        """
        Resolve the directory this pattern copies from.

        Returns:
            `source` if set, otherwise the bundled project template.

        Raises:
            ValueError: If `source` is set but is not a directory.
        """
        if self.source is None:
            return _TEMPLATE_DIR
        if not self.source.is_dir():
            msg = f"pattern source is not a directory: {self.source}"
            raise ValueError(msg)
        return self.source

    def _scaffold(self, destination: Path, *, dry_run: bool = False) -> None:
        """
        Copy the source tree into `destination`.

        Args:
            destination: Directory in which to create the project.
            dry_run: If `True`, perform no filesystem writes.
        """
        if dry_run:
            return
        destination.mkdir(parents=True, exist_ok=True)
        self._copy_template_tree(self._source_dir(), destination)

    def plan(self) -> str:
        """
        Describe the source tree this pattern copies.

        Returns:
            A text tree of the source's files and directories.
        """
        return self._render_tree(self._source_dir())

    def conflicts(self, destination: Path) -> list[Path]:
        """
        List files under `destination` that copying the source would overwrite.

        Args:
            destination: The directory the project would be created in.

        Returns:
            Paths, relative to the source, that already exist under `destination`.
        """
        source = self._source_dir()
        found: list[Path] = []
        for item in source.rglob("*"):
            if not item.is_file() or "__pycache__" in item.parts:
                continue
            relative = item.relative_to(source)
            if (destination / relative).exists():
                found.append(relative)
        return found
