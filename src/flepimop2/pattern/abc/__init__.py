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
"""Abstract base class for flepimop2 project patterns."""

__all__ = ["PatternABC", "build"]

from abc import abstractmethod
from pathlib import Path
from typing import Any

from flepimop2._utils._module import _build
from flepimop2.module import ModuleBase


class PatternABC(ModuleBase, module_namespace="pattern"):
    """
    Abstract base class for flepimop2 project patterns.

    A pattern materializes a starting project at a destination directory. The
    bundled `pattern.default` scaffolds from a template; other patterns can, for
    example, clone and activate an existing project (see #251). New project
    sources plug in by implementing `_scaffold`, so the CLI and any callers stay
    agnostic to where the project comes from.
    """

    def scaffold(self, destination: Path, *, dry_run: bool = False) -> None:
        """
        Materialize this pattern's project at `destination`.

        Args:
            destination: Directory in which to create the project.
            dry_run: If `True`, perform no filesystem writes.
        """
        return self._scaffold(destination, dry_run=dry_run)

    @abstractmethod
    def _scaffold(self, destination: Path, *, dry_run: bool = False) -> None:
        """Pattern-specific implementation for materializing the project."""
        ...

    @staticmethod
    def _copy_template_tree(source: Path, destination: Path) -> None:
        """
        Recursively copy a template directory structure to a destination.

        Args:
            source: The source template directory to copy from.
            destination: The destination directory to copy to.

        Examples:
            >>> from pathlib import Path
            >>> from flepimop2.pattern.abc import PatternABC
            >>> test_dir = Path.cwd() / "copy_tree_test"
            >>> test_dir.mkdir(exist_ok=True)
            >>> source = test_dir / "source"
            >>> source.mkdir(exist_ok=True)
            >>> (source / "config.yaml").write_text("key: value")
            10
            >>> (source / "subdir").mkdir(exist_ok=True)
            >>> (source / "subdir" / "data.txt").write_text("test data")
            9
            >>> dest = test_dir / "dest"
            >>> dest.mkdir(exist_ok=True)
            >>> PatternABC._copy_template_tree(source, dest)
            >>> (dest / "config.yaml").read_text()
            'key: value'
            >>> (dest / "subdir" / "data.txt").read_text()
            'test data'

        """
        for item in source.iterdir():
            dest_item = destination / item.name
            if item.is_dir():
                dest_item.mkdir(parents=True, exist_ok=True)
                PatternABC._copy_template_tree(item, dest_item)
            else:
                dest_item.write_text(item.read_text())


def build(config: dict[str, Any] | ModuleBase | str) -> PatternABC:
    """
    Build a `PatternABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary, `ModuleBase` instance, or shorthand
            string. The configuration must declare a `module`, which is resolved
            under `flepimop2.pattern.` when given as a short name.

    Returns:
        The constructed pattern instance.
    """
    return _build(config, "pattern", PatternABC)  # type: ignore[type-abstract]
