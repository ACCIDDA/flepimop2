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
"""The bundled copy pattern: scaffold a project from a directory or archive."""

__all__ = ["CopyPattern"]

import stat
import tarfile
import tempfile
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from flepimop2.pattern.abc import PatternABC

_TEMPLATE_DIR = Path(__file__).parents[2] / "templates" / "skeleton"


class CopyPattern(PatternABC, module="copy"):
    """Scaffold a project by copying a source tree.

    The `source` directory or zip/tar archive is copied verbatim into the target.
    It defaults to the bundled project template, so `flepimop2 pattern` with no
    `--source` produces the documented quickstart; point `source` at another
    project or a local archive to pattern off it instead.
    """

    # Directory or archive to copy from; None uses the bundled project template.
    source: Path | None = None

    @staticmethod
    def _safe_member_path(name: str) -> PurePosixPath:
        """
        Validate and normalize an archive member path.

        Args:
            name: Member name stored in an archive.

        Returns:
            A normalized relative POSIX path.

        Raises:
            ValueError: If the member could escape the extraction directory.
        """
        path = PurePosixPath(name.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            msg = f"archive member escapes the target directory: {name}"
            raise ValueError(msg)
        return path

    @classmethod
    def _unpack_archive(cls, source: Path, destination: Path) -> None:
        """
        Safely unpack a local zip or tar archive.

        Args:
            source: Archive to unpack.
            destination: Temporary directory receiving the archive contents.

        Raises:
            ValueError: If the format is unsupported or contains unsafe links or
                paths.
        """
        if zipfile.is_zipfile(source):
            with zipfile.ZipFile(source) as archive:
                for zip_member in archive.infolist():
                    cls._safe_member_path(zip_member.filename)
                    mode = zip_member.external_attr >> 16
                    if stat.S_ISLNK(mode):
                        msg = f"archive links are not supported: {zip_member.filename}"
                        raise ValueError(msg)
                archive.extractall(destination)  # noqa: S202
            return
        if tarfile.is_tarfile(source):
            with tarfile.open(source) as archive:
                for tar_member in archive.getmembers():
                    cls._safe_member_path(tar_member.name)
                    if tar_member.issym() or tar_member.islnk():
                        msg = f"archive links are not supported: {tar_member.name}"
                        raise ValueError(msg)
                    if not tar_member.isfile() and not tar_member.isdir():
                        msg = f"archive member type is not supported: {tar_member.name}"
                        raise ValueError(msg)
                archive.extractall(destination, filter="fully_trusted")  # noqa: S202
            return
        msg = f"pattern source is not a supported zip or tar archive: {source}"
        raise ValueError(msg)

    @contextmanager
    def _source_tree(self) -> Iterator[Path]:
        """
        Resolve the directory tree this pattern copies from.

        Yields:
            `source` when it is a directory, the bundled template when unset, or
            a temporary extraction directory when `source` is an archive.

        Raises:
            ValueError: If `source` is missing or is not a supported archive.
        """
        if self.source is None:
            yield _TEMPLATE_DIR
            return
        if self.source.is_dir():
            yield self.source
            return
        if not self.source.is_file():
            msg = f"pattern source does not exist: {self.source}"
            raise ValueError(msg)
        with tempfile.TemporaryDirectory() as temporary_directory:
            extracted = Path(temporary_directory)
            self._unpack_archive(self.source, extracted)
            yield extracted

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
        with self._source_tree() as source:
            self._copy_template_tree(source, destination)

    def plan(self) -> str:
        """
        Describe the source tree this pattern copies.

        Returns:
            A text tree of the source's files and directories.
        """
        with self._source_tree() as source:
            return self._render_tree(source)

    def conflicts(self, destination: Path) -> list[Path]:
        """
        List files under `destination` that copying the source would overwrite.

        Args:
            destination: The directory the project would be created in.

        Returns:
            Paths, relative to the source, that already exist under `destination`.
        """
        found: list[Path] = []
        with self._source_tree() as source:
            for item in source.rglob("*"):
                if not item.is_file() or "__pycache__" in item.parts:
                    continue
                relative = item.relative_to(source)
                if (destination / relative).exists():
                    found.append(relative)
        return found
