"""Unit tests for `_load_builder` function."""

from pathlib import Path
from shutil import copy
from types import ModuleType
from typing import Final
from unittest.mock import MagicMock, patch

import pytest

from flepimop2._utils._module import _load_builder, _load_module

FIXTURE_DIR: Final = Path(__file__).with_suffix("")


def test_load_builder_attribute_error() -> None:
    """Test AttributeError is raised with no build function or target class."""
    # Mock import_module to return a module without build function
    mock_module = MagicMock(spec=[])

    with (
        patch("flepimop2._utils._module.import_module", return_value=mock_module),
        patch("flepimop2._utils._module._validate_function", return_value=False),
        patch("flepimop2._utils._module._find_target_class", return_value=None),
        pytest.raises(
            AttributeError,
            match=r"Module 'test_module' does not have a valid 'build' function\.",
        ),
    ):
        _load_builder("test_module")


def test_load_builder_with_existing_build_function(tmp_path: Path) -> None:
    """Test that module with existing build function is loaded correctly."""
    # Copy fixture to tmp_path
    fixture_file = tmp_path / "module_with_build.py"
    copy(FIXTURE_DIR / "module_with_build.py", fixture_file)

    # Mock import_module to load from the fixture file
    def mock_import(mod_name: str) -> ModuleType:
        return _load_module(fixture_file, mod_name)

    with patch("flepimop2._utils._module.import_module", side_effect=mock_import):
        mod = _load_builder("module_with_build")

    # Verify the module has the build function
    assert hasattr(mod, "build")
    assert callable(mod.build)
    # Test that it's the original build function, not auto-generated
    result = mod.build({"test": "value"})
    assert result == {"test": "value", "from": "original_build"}


def test_load_builder_creates_default_build_for_basemodel(tmp_path: Path) -> None:
    """Test that build function is auto-generated for BaseModel subclass."""
    # Copy fixture to tmp_path
    fixture_file = tmp_path / "module_with_basemodel.py"
    copy(FIXTURE_DIR / "module_with_basemodel.py", fixture_file)

    # Mock import_module to load from the fixture file
    def mock_import(mod_name: str) -> ModuleType:
        return _load_module(fixture_file, mod_name)

    with patch("flepimop2._utils._module.import_module", side_effect=mock_import):
        mod = _load_builder("module_with_basemodel")

    # Verify the module now has a build function
    assert hasattr(mod, "build")
    assert callable(mod.build)
    # Test that the auto-generated build function works
    result = mod.build({"name": "test", "value": 42})
    assert result.name == "test"
    assert result.value == 42
