"""Unit tests for SkeletonCommand._copy_template_tree method."""

from pathlib import Path

from flepimop2._cli._skeleton_command import SkeletonCommand


def test_copy_empty_directory(tmp_path: Path) -> None:
    """Test copying an empty directory."""
    source = tmp_path / "source"
    source.mkdir()
    dest = tmp_path / "dest"
    dest.mkdir()
    SkeletonCommand._copy_template_tree(source, dest)
    assert dest.exists()
    assert list(dest.iterdir()) == []


def test_copy_mixed_structure(tmp_path: Path) -> None:
    """Test copying a complex directory structure with files and subdirectories."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "root_file.txt").write_text("Root content")
    (source / "config").mkdir()
    (source / "config" / "example.yaml").write_text("key: value")
    (source / "config" / "foobar.yaml").write_text("abc: def")
    (source / "data").mkdir()
    (source / "data" / "input").mkdir()
    (source / "data" / "input" / "data.csv").write_text("col1,col2\n1,2")
    (source / "data" / "output").mkdir()
    (source / "data" / "output" / ".gitkeep").write_text("")
    dest = tmp_path / "dest"
    dest.mkdir()
    SkeletonCommand._copy_template_tree(source, dest)
    assert (dest / "root_file.txt").read_text() == "Root content"
    assert (dest / "config").is_dir()
    assert (dest / "config" / "example.yaml").read_text() == "key: value"
    assert (dest / "config" / "foobar.yaml").read_text() == "abc: def"
    assert (dest / "data").is_dir()
    assert (dest / "data" / "input").is_dir()
    assert (dest / "data" / "input" / "data.csv").read_text() == "col1,col2\n1,2"
    assert (dest / "data" / "output").is_dir()
    assert not (dest / "data" / "output" / ".gitkeep").read_text()
