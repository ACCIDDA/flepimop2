"""Unit tests for `_load_builder` function."""

from pathlib import Path
from shutil import copy
from types import ModuleType
from typing import Any, Final
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from flepimop2._utils._module import _load_builder, _load_module
from flepimop2.module import ModuleABC

FIXTURE_DIR: Final = Path(__file__).parent / "_load_builder_assets"


def test_load_builder_attribute_error() -> None:
    """Test AttributeError is raised with no build function or target class."""
    mock_module = ModuleType("test_module")

    with (
        patch("flepimop2._utils._module.import_module", return_value=mock_module),
        pytest.raises(
            AttributeError,
            match=(
                r"Module 'test_module' does not have a ModuleABC class "
                r"which is also a pydantic BaseModel\."
            ),
        ),
    ):
        _load_builder("test_module", ModuleABC)


def test_load_builder_with_existing_build_function(tmp_path: Path) -> None:
    """Test that module with existing build function is loaded correctly."""
    # Copy fixture to tmp_path
    fixture_file = tmp_path / "module_with_build.py"
    copy(FIXTURE_DIR / "module_with_build.py", fixture_file)

    # Mock import_module to load from the fixture file
    def mock_import(mod_name: str) -> ModuleType:
        return _load_module(fixture_file, mod_name)

    with patch("flepimop2._utils._module.import_module", side_effect=mock_import):
        mod: Any = _load_builder("module_with_build", ModuleABC)

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
        mod: Any = _load_builder("module_with_basemodel", ModuleABC)

    # Verify the module now has a build function
    assert hasattr(mod, "build")
    assert callable(mod.build)
    # Test that the auto-generated build function works
    result: Any = mod.build({"name": "test", "value": 42})
    assert isinstance(result, BaseModel)
    result_model: Any = result
    assert result_model.name == "test"
    assert result_model.value == 42
