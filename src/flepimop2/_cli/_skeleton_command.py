"""Skeleton command implementation."""

__all__ = []

import os
from pathlib import Path

from flepimop2._cli._cli_command import CliCommand


class SkeletonCommand(CliCommand):
    """
    Create a project skeleton with directory structure and template files.

    This command scaffolds a new flepimop2 project by creating the necessary
    directory structure and populating it with template configuration files,
    environment specifications, and other boilerplate files needed to get started.

    The `PATH` argument specifies where to create the project. If omitted, the
    skeleton will be created in the current working directory.

    \b
    Examples:
        # Create an empty project in a new directory
        $ flepimop2 skeleton foobar
        # Create a project in the current directory
        $ mkdir fizzbuzz && cd fizzbuzz
        $ flepimop2 skeleton

    """  # noqa: D301

    def run(  # type: ignore[override]
        self,
        *,
        path: Path | None,
        dry_run: bool,
    ) -> None:
        """
        Create a project skeleton.

        Args:
            path: Path to the new project.
            dry_run: Whether to perform a dry run.

        """
        path = path or Path.cwd()
        if not path.exists():
            parent_dir = path.parent
            while not parent_dir.exists():
                parent_dir = parent_dir.parent
            if os.access(parent_dir, os.W_OK) is False:
                self.error(f"Cannot write to path: {path}")
                return

        if dry_run:
            self.info(f"Would create skeleton project at: {path}")
            return
        path.mkdir(parents=True, exist_ok=True)
        template_dir = Path(__file__).parent.parent / "templates" / "skeleton"
        self._copy_template_tree(template_dir, path)
        self.info(f"Skeleton project created at: {path}")
        self.info(f"Directory structure:\n{self._generate_tree(path)}")

    @staticmethod
    def _copy_template_tree(source: Path, destination: Path) -> None:
        """
        Recursively copy template directory structure to destination.

        Args:
            source: The source template directory to copy from.
            destination: The destination directory to copy to.

        Examples:
            >>> from pathlib import Path
            >>> from flepimop2._cli._skeleton_command import SkeletonCommand
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
            >>> SkeletonCommand._copy_template_tree(source, dest)
            >>> (dest / "config.yaml").read_text()
            'key: value'
            >>> (dest / "subdir" / "data.txt").read_text()
            'test data'

        """
        for item in source.iterdir():
            dest_item = destination / item.name
            if item.is_dir():
                dest_item.mkdir(parents=True, exist_ok=True)
                SkeletonCommand._copy_template_tree(item, dest_item)
            else:
                dest_item.write_text(item.read_text())

    @staticmethod
    def _generate_tree(directory: Path, prefix: str = "") -> str:
        """
        Generate ASCII tree representation of directory structure.

        Args:
            directory: The root directory to generate the tree from.
            prefix: The prefix for the current level (used in recursion).

        Returns:
            A string representing the directory tree.

        Examples:
            >>> from pathlib import Path
            >>> from flepimop2._cli._skeleton_command import SkeletonCommand
            >>> example_dir = Path.cwd() / "tree_example"
            >>> example_dir.mkdir(exist_ok=True)
            >>> (example_dir / "file.txt").write_text("Sample file")
            11
            >>> (example_dir / "subdir").mkdir(exist_ok=True)
            >>> (example_dir / "subdir" / "file1.txt").write_text("Sample file 1")
            13
            >>> print(SkeletonCommand._generate_tree(example_dir))
            ├── subdir
            │   └── file1.txt
            └── file.txt
            <BLANKLINE>

        """
        tree = ""
        try:
            items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except (OSError, PermissionError):
            return tree
        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            current_prefix = "└── " if is_last_item else "├── "
            tree += f"{prefix}{current_prefix}{item.name}\n"
            if item.is_dir():
                next_prefix = prefix + ("    " if is_last_item else "│   ")
                tree += SkeletonCommand._generate_tree(item, next_prefix)
        return tree
