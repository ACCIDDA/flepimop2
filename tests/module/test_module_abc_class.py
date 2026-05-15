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
"""Tests for `ModuleBase` class behavior."""

from typing import Literal, get_args

import numpy as np
import pytest
from pydantic import ValidationError

from flepimop2.backend.abc import BackendABC
from flepimop2.module import ModuleBase
from flepimop2.process.abc import ProcessABC
from flepimop2.typing import Float64NDArray, PatchConflictMode


def test_missing_module_attribute_raises() -> None:
    """Concrete subclasses must define `module`."""
    with pytest.raises(
        TypeError,
        match="must define class attribute 'module' as a non-empty string",
    ):

        class MissingModule(ModuleBase):
            pass


def test_invalid_module_value_raises() -> None:
    """Concrete subclasses must define `module` as a non-empty Literal field."""
    with pytest.raises(
        (TypeError, Exception),
        match="must define class attribute 'module' as a non-empty string",
    ):
        # Providing an annotated but empty module value triggers our check.
        class InvalidModule(ModuleBase):
            module: str = ""


def test_module_shortcut_sets_fully_qualified_module() -> None:
    """The class-definition shortcut should resolve namespaced modules."""

    class MyProcess(ProcessABC, module="test_process"):
        def _process(self, *, dry_run: bool) -> None: ...

    mod = MyProcess()
    assert mod.module == "flepimop2.process.test_process"


def test_module_shortcut_sets_fully_qualified_module_for_backend_subclass() -> None:
    """The class-definition shortcut should resolve namespaced backends."""

    class MyBackend(BackendABC, module="test_backend"):
        def _save(self, data: Float64NDArray, run_meta: object) -> None: ...

        def _read(self, _run_meta: object) -> Float64NDArray:
            return np.array([], dtype=np.float64)

    mod = MyBackend()
    assert mod.module == "flepimop2.backend.test_backend"


def test_module_namespace_keyword_sets_public_classvar() -> None:
    """The class-definition namespace shortcut should set `module_namespace`."""

    class PluginModule(ModuleBase, module_namespace="plugin", module="demo"):
        pass

    assert PluginModule.module_namespace == "plugin"
    assert PluginModule.model_fields["module"].default == "flepimop2.plugin.demo"


def test_short_module_name_requires_module_namespace() -> None:
    """Short module names should fail without a declared namespace."""
    with pytest.raises(
        TypeError,
        match="must define `module_namespace` to use the class keyword argument",
    ):

        class MissingNamespaceModule(ModuleBase, module="demo"):
            pass


def test_module_namespace_keyword_and_explicit_attribute_conflict_raises() -> None:
    """Namespace shortcut cannot be combined with an explicit class-body attribute."""
    with pytest.raises(
        TypeError,
        match="cannot define both class attribute 'module_namespace'",
    ):

        class ConflictingNamespaceModule(ModuleBase, module_namespace="plugin"):
            module_namespace = "other"


def test_module_shortcut_sets_literal_module_field() -> None:
    """The shortcut should specialise the Pydantic `module` field to a Literal."""

    class MyBackend(BackendABC, module="test_backend"):
        root: str = "."

        def _save(self, data: object, run_meta: object) -> None: ...

        def _read(self, _run_meta: object) -> Float64NDArray:
            return np.array([], dtype=np.float64)

    expected = "flepimop2.backend.test_backend"

    assert get_args(MyBackend.model_fields["module"].annotation) == (expected,)
    assert MyBackend.model_fields["module"].default == expected
    assert MyBackend.model_validate({"root": "."}).module == expected
    with pytest.raises(ValidationError, match="Input should be"):
        MyBackend.model_validate({"module": "wrong", "root": "."})


def test_module_shortcut_allows_instantiation_without_module_argument() -> None:
    """Shortcut-backed subclasses should not require `module` at init time."""

    class MyBackend(BackendABC, module="test_backend"):
        root: str = "."

        def _save(self, data: object, run_meta: object) -> None: ...

        def _read(self, _run_meta: object) -> Float64NDArray:
            return np.array([], dtype=np.float64)

    assert MyBackend(root=".").module == "flepimop2.backend.test_backend"


def test_module_shortcut_and_explicit_attribute_conflict_raises() -> None:
    """The shortcut cannot be combined with an explicit class-body string attribute."""
    with pytest.raises(
        TypeError,
        match="cannot define both class attribute 'module' and class keyword argument",
    ):

        class ConflictingProcess(ProcessABC, module="test_process"):
            module: str = "flepimop2.process.test_process"

            def _process(self, *, dry_run: bool) -> None: ...


def test_option_reports_missing_option_by_module_name() -> None:
    """Option lookup should raise KeyError with module name for missing options."""

    class MyModule(ModuleBase, module="flepimop2.test.mymodule"):
        pass

    mod = MyModule()
    with pytest.raises(
        KeyError,
        match=r"Option 'missing' not found in module 'flepimop2.test.mymodule'",
    ):
        mod.option("missing")


def test_option_reads_existing_value() -> None:
    """Option lookup should return configured values."""

    class MyModule(ModuleBase, module="flepimop2.test.mymodule"):
        pass

    mod = MyModule.model_validate({"options": {"alpha": 42, "enabled": False}})
    assert mod.option("alpha") == 42
    assert mod.option("enabled") is False


def test_option_uses_default_when_missing() -> None:
    """Missing options should return the provided default."""

    class MyModule(ModuleBase, module="flepimop2.test.mymodule"):
        pass

    mod = MyModule()
    assert mod.options is None
    assert mod.option("missing", default=0) == 0


def test_module_patch_replace_returns_other() -> None:
    """Replace mode should return the incoming patch model."""
    mod = ModuleBase.model_validate({
        "module": "fixed",
        "value": [1, 2, 3],
        "shape": "age",
    })
    patch = ModuleBase.model_validate({"module": "fixed", "value": [4, 5, 6]})

    replaced = mod.patch(patch, conflict=PatchConflictMode.REPLACE)

    assert replaced is not patch
    assert replaced.model_dump(exclude_none=True) == {
        "module": "fixed",
        "value": [4, 5, 6],
    }


def test_module_patch_merge_deep_merges_model_dumps() -> None:
    """Merge mode should deep-merge the dumped model dictionaries."""
    mod = ModuleBase.model_validate({
        "module": "fixed",
        "value": [1, 2, 3],
        "shape": "age",
    })
    patch = ModuleBase.model_validate({"module": "fixed", "value": [4, 5, 6]})

    merged = mod.patch(patch, conflict=PatchConflictMode.MERGE)

    assert merged.model_dump(exclude_none=True) == {
        "module": "fixed",
        "value": [4, 5, 6],
        "shape": "age",
    }


def test_module_patch_raises_type_error_for_mismatched_model_types() -> None:
    """Default module patching should reject different concrete model types."""

    class FirstModule(ModuleBase, module="flepimop2.test.first"):
        pass

    class SecondModule(ModuleBase, module="flepimop2.test.second"):
        pass

    mod: ModuleBase = FirstModule()
    patch = SecondModule()

    with pytest.raises(TypeError, match="requires matching concrete types"):
        mod.patch(patch, conflict=PatchConflictMode.MERGE)


def test_explicit_module_definition_still_works() -> None:
    """Subclasses may still define `module` as a Literal field directly."""

    class MyProcess(ProcessABC):
        module: Literal["flepimop2.process.explicit"] = "flepimop2.process.explicit"
        command: str = "echo"

        def _process(self, *, dry_run: bool) -> None: ...

    expected = "flepimop2.process.explicit"

    assert MyProcess().module == expected
    assert get_args(MyProcess.model_fields["module"].annotation) == (expected,)
