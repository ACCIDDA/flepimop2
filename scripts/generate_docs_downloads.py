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
"""Generate downloadable project ZIP bundles for the documentation site."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = PROJECT_ROOT / "docs"
DOWNLOADS_ROOT = DOCS_ROOT / "downloads"
SKELETON_ROOT = PROJECT_ROOT / "src" / "flepimop2" / "templates" / "skeleton"


def _bundle_asset_dirs() -> tuple[Path, ...]:
    """
    Find the subdirectories of the "assets" directory that should be ZIP bundles.

    Returns:
        A tuple of Paths to the asset directories, sorted by name.
    """
    return tuple(
        sorted(
            (
                path
                for path in (DOCS_ROOT / "assets").iterdir()
                if path.is_dir() and not path.name.startswith("__")
            ),
            key=lambda path: path.name,
        )
    )


def _copy_project_template(destination: Path) -> None:
    """
    Copy the base skeleton project tree to the destination.

    Args:
        destination: The path to copy the skeleton project to.
    """
    shutil.copytree(
        SKELETON_ROOT,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )


def _apply_overlays(destination: Path, asset_dir: Path) -> None:
    """
    Copy guide-specific directory trees into the generated project tree.

    Args:
        destination: The path to copy the overlays to.
        asset_dir: The path to the asset directory containing the overlays.
    """
    # Dereference symlinks so downloadable bundles contain plain files even if
    # docs/assets deduplicates shared content with links in the repository.
    shutil.copytree(
        asset_dir,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".gitkeep"),
    )


def _write_directory_to_zip(bundle_root: Path, zip_path: Path) -> None:
    """
    Write a project directory tree to a ZIP archive, preserving empty dirs.

    Args:
        bundle_root: The root directory of the project to be zipped.
        zip_path: The path to the output ZIP file.
    """
    with ZipFile(zip_path, mode="w", compression=ZIP_DEFLATED) as zip_file:
        for current_root, _dirnames, filenames in os.walk(bundle_root):
            root = Path(current_root)
            relative_root = root.relative_to(bundle_root.parent)
            if root != bundle_root:
                zip_file.writestr(f"{relative_root.as_posix()}/", "")

            for filename in sorted(filenames):
                if filename == ".gitkeep":
                    continue
                source_path = root / filename
                relative_file = relative_root / filename
                zip_file.write(source_path, arcname=relative_file.as_posix())


def generate_downloads() -> None:
    """Generate all documentation ZIP bundles."""
    DOWNLOADS_ROOT.mkdir(parents=True, exist_ok=True)
    for zip_path in DOWNLOADS_ROOT.glob("*.zip"):
        zip_path.unlink()

    with tempfile.TemporaryDirectory(prefix="flepimop2-docs-downloads-") as temp_dir:
        temp_root = Path(temp_dir)
        for asset_dir in _bundle_asset_dirs():
            bundle_root = temp_root / asset_dir.name
            _copy_project_template(bundle_root)
            _apply_overlays(bundle_root, asset_dir)
            _write_directory_to_zip(
                bundle_root,
                DOWNLOADS_ROOT / f"{asset_dir.name}.zip",
            )


if __name__ == "__main__":
    generate_downloads()
