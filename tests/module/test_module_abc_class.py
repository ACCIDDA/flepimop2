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
from typing import Any, Literal

import pytest

from flepimop2.configuration import ModuleModel
from flepimop2.module import ModuleABC


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
