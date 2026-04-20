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
"""Tests for `ModuleABC` class behavior."""

from abc import ABC, abstractmethod
from typing import Any, Literal, get_args

import numpy as np
import pytest
from pydantic import ValidationError

from flepimop2.backend.abc import BackendABC
from flepimop2.configuration import ModuleModel
from flepimop2.module import ModuleABC
from flepimop2.process.abc import ProcessABC
from flepimop2.typing import Float64NDArray


def test_missing_module_attribute_raises() -> None:
    """Concrete subclasses must define `module`."""
    with pytest.raises(
        TypeError,
        match="must define class attribute 'module' as a non-empty string",
    ):

        class MissingModule(ModuleABC):
            pass


@pytest.mark.parametrize("bad_module", ["", 1])
def test_invalid_module_value_raises(bad_module: object) -> None:
    """Concrete subclasses must define `module` as a non-empty string."""
    with pytest.raises(
        TypeError,
        match="must define class attribute 'module' as a non-empty string",
    ):

        class InvalidModule(ModuleABC):
            module = bad_module  # type: ignore[assignment]


def test_abstract_subclass_can_skip_module() -> None:
    """Abstract subclasses may defer module specification."""

    class AbstractModule(ModuleABC, ABC):
        @abstractmethod
        def do_thing(self) -> None: ...

    class ConcreteModule(AbstractModule):
        module = "flepimop2.test.module"

        def do_thing(self) -> None: ...

    assert ConcreteModule().module == "flepimop2.test.module"


def test_option_reports_module_for_plain_subclass() -> None:
    """Option lookup should include module name for plain subclasses."""

    class PlainModule(ModuleABC):
        module = "flepimop2.test.module"

    mod = PlainModule()
    with pytest.raises(
        KeyError, match=r"Option 'missing' not found in module 'flepimop2.test.module'"
    ):
        mod.option("missing")


def test_option_reads_existing_value_for_plain_subclass() -> None:
    """Option lookup should return configured values for plain subclasses."""

    class PlainModule(ModuleABC):
        module = "flepimop2.test.module"

        def __init__(self, **options: Any) -> None:
            super().__init__()
            self.options = options

    mod = PlainModule(alpha=1.5, enabled=True)
    assert mod.option("alpha") == pytest.approx(1.5)
    assert mod.option("enabled") is True


def test_option_uses_default_when_missing_for_plain_subclass() -> None:
    """Missing options should return the provided default for plain subclasses."""

    class PlainModule(ModuleABC):
        module = "flepimop2.test.module"

    mod = PlainModule()
    assert mod.option("missing", default="fallback") == "fallback"


def test_module_shortcut_sets_fully_qualified_module_for_plain_subclass() -> None:
    """The class-definition shortcut should resolve namespaced plain modules."""

    class PlainProcess(ProcessABC, module="test_process"):
        def _process(self, *, dry_run: bool) -> None: ...

    mod = PlainProcess()
    assert mod.module == "flepimop2.process.test_process"


def test_module_shortcut_sets_fully_qualified_module_for_plain_backend_subclass() -> (
    None
):
    """The class-definition shortcut should resolve namespaced plain backends."""

    class PlainBackend(BackendABC, module="test_backend"):
        def _save(self, data: Float64NDArray, run_meta: object) -> None: ...

        def _read(self, _run_meta: object) -> Float64NDArray:
            return np.array([], dtype=np.float64)

    mod = PlainBackend()
    assert mod.module == "flepimop2.backend.test_backend"


def test_module_namespace_keyword_sets_public_classvar() -> None:
    """The class-definition namespace shortcut should set `module_namespace`."""

    class PluginModule(ModuleABC, module_namespace="plugin", module="demo"):
        pass

    assert PluginModule.module_namespace == "plugin"
    assert PluginModule.module == "flepimop2.plugin.demo"


def test_short_module_name_requires_module_namespace() -> None:
    """Short module names should fail without a declared namespace."""
    with pytest.raises(
        TypeError,
        match="must define `module_namespace` to use the class keyword argument",
    ):

        class MissingNamespaceModule(ModuleABC, module="demo"):
            pass


def test_module_namespace_keyword_and_explicit_attribute_conflict_raises() -> None:
    """The namespace shortcut cannot be combined with an explicit attribute."""
    with pytest.raises(
        TypeError,
        match="cannot define both class attribute 'module_namespace'",
    ):

        class ConflictingNamespaceModule(ModuleABC, module_namespace="plugin"):
            module_namespace = "other"
            module = "flepimop2.plugin.demo"


def test_module_shortcut_sets_literal_module_field_for_pydantic_subclass() -> None:
    """The shortcut should also specialize the Pydantic `module` field."""

    class PydanticBackend(ModuleModel, BackendABC, module="test_backend"):
        root: str = "."

        def _save(self, data: object, run_meta: object) -> None: ...

        def _read(self, _run_meta: object) -> Float64NDArray:
            return np.array([], dtype=np.float64)

    expected = "flepimop2.backend.test_backend"

    assert get_args(PydanticBackend.model_fields["module"].annotation) == (expected,)
    assert PydanticBackend.model_fields["module"].default == expected
    assert PydanticBackend.model_validate({"root": "."}).module == expected
    with pytest.raises(ValidationError, match="Input should be"):
        PydanticBackend.model_validate({"module": "wrong", "root": "."})


def test_module_shortcut_allows_pydantic_instantiation_without_module_argument() -> (
    None
):
    """Shortcut-backed Pydantic subclasses should not require `module` at init time."""

    class PydanticBackend(ModuleModel, BackendABC, module="test_backend"):
        root: str = "."

        def _save(self, data: object, run_meta: object) -> None: ...

        def _read(self, _run_meta: object) -> Float64NDArray:
            return np.array([], dtype=np.float64)

    assert PydanticBackend(root=".").module == "flepimop2.backend.test_backend"


def test_module_shortcut_and_explicit_attribute_conflict_raises() -> None:
    """The shortcut cannot be combined with an explicit class `module` attribute."""
    with pytest.raises(
        TypeError,
        match="cannot define both class attribute 'module' and class keyword argument",
    ):

        class ConflictingProcess(ProcessABC, module="test_process"):
            module = "flepimop2.process.test_process"

            def _process(self, *, dry_run: bool) -> None: ...


def test_option_reports_module_for_pydantic_subclass() -> None:
    """Option lookup should include module name for pydantic subclasses."""

    class PydanticModule(ModuleModel, ModuleABC):
        module: Literal["flepimop2.test.module"] = "flepimop2.test.module"

    mod = PydanticModule()
    assert mod.module == "flepimop2.test.module"
    with pytest.raises(
        KeyError, match=r"Option 'missing' not found in module 'flepimop2.test.module'"
    ):
        mod.option("missing")


def test_option_reads_existing_value_for_pydantic_subclass() -> None:
    """Option lookup should use parsed `options` values for pydantic subclasses."""

    class PydanticModule(ModuleModel, ModuleABC):
        module: Literal["flepimop2.test.module"] = "flepimop2.test.module"

    mod = PydanticModule.model_validate({"options": {"alpha": 42, "enabled": False}})
    assert mod.option("alpha") == 42
    assert mod.option("enabled") is False


def test_option_uses_default_when_missing_for_pydantic_subclass() -> None:
    """Missing options should return the provided default for pydantic subclasses."""

    class PydanticModule(ModuleModel, ModuleABC):
        module: Literal["flepimop2.test.module"] = "flepimop2.test.module"

    mod = PydanticModule()
    assert mod.options is None
    assert mod.option("missing", default=0) == 0


def test_explicit_module_definition_still_works_for_plain_subclass() -> None:
    """Plain subclasses may still define `module` directly."""

    class PlainProcess(ProcessABC):
        module = "flepimop2.process.explicit"

        def _process(self, *, dry_run: bool) -> None: ...

    assert PlainProcess().module == "flepimop2.process.explicit"


def test_explicit_module_definition_still_works_for_pydantic_subclass() -> None:
    """Pydantic subclasses may still define `module` directly."""

    class PydanticProcess(ModuleModel, ProcessABC):
        module: Literal["flepimop2.process.explicit"] = "flepimop2.process.explicit"
        command: str = "echo"

        def _process(self, *, dry_run: bool) -> None: ...

    expected = "flepimop2.process.explicit"

    assert PydanticProcess().module == expected
    assert get_args(PydanticProcess.model_fields["module"].annotation) == (expected,)
