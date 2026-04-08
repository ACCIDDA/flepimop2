"""Unit tests for `_find_target_class` function."""

from pathlib import Path
from shutil import copy
from typing import Any, Final

import pytest
from pydantic import BaseModel

from flepimop2._utils._module import _find_target_class, _load_module
from flepimop2.module import ModuleABC

FIXTURE_DIR: Final = Path(__file__).parent / "_find_target_class_assets"


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("valid_basemodel.py", "TestModel"),
        ("no_classes.py", None),
        ("abc_only.py", None),
    ],
)
def test_find_target_class(tmp_path: Path, fixture: str, expected: str | None) -> None:
    """Test `_find_target_class` returns with various fixtures."""
    # Prepare test module
    module_name = fixture.split(".", maxsplit=1)[0]
    test_file = tmp_path / fixture
    copy(FIXTURE_DIR / fixture, test_file)
    # Load module and find target class
    mod = _load_module(test_file, module_name)
    # Verify results
    if expected is None:
        with pytest.raises(
            AttributeError,
            match=(
                rf"Module '{module_name}' does not have a ModuleABC class "
                r"which is also a pydantic BaseModel\."
            ),
        ):
            _find_target_class(mod, module_name, ModuleABC)
    else:
        target_class: Any = _find_target_class(mod, module_name, ModuleABC)
        assert issubclass(target_class, BaseModel)
        assert issubclass(target_class, ModuleABC)
        assert target_class.__name__ == expected
        assert hasattr(target_class, "model_validate")
