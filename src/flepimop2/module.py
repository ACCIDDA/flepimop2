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
"""Base class for defining flepimop2 modules."""

__all__ = ["ModuleBase"]

import inspect
from typing import Any, ClassVar, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field

from flepimop2._utils._dict import _deep_merge_dicts
from flepimop2.typing import PatchConflictMode, RaiseOnMissing, RaiseOnMissingType
from flepimop2.yaml import _model_to_yaml_mapping


class ModuleBase(BaseModel):
    """
    Base class for all flepimop2 modules.

    Combines configuration parsing via `pydantic` with the module-naming
    conventions required by the `flepimop2` loader.  Every concrete module
    class must end up with a non-empty `module` string - either declared
    explicitly as a `Literal[...]` field or resolved from the
    `module="..."` class-keyword shortcut.

    Attributes:
        module_namespace: The `flepimop2` namespace used to resolve short module
            names such as `"csv"` into fully-qualified paths like
            `"flepimop2.backend.csv"`.  Set by the ABC subclass, not by
            individual module implementations.
        module: The fully-qualified module name.  Concrete subclasses should
            specialize this to a `Literal[...]` type via the `module="..."`
            class-keyword shortcut.
        options: Optional grab-bag of extra information the module exposes for
            `flepimop2` to take advantage of.

    """

    model_config = ConfigDict(extra="allow")

    module_namespace: ClassVar[str | None] = None
    # _pending_module stores a shortcut value set via module="..." keyword
    # during __init_subclass__ and consumed by __pydantic_init_subclass__ once
    # Pydantic has finished building the model.
    _pending_module: ClassVar[str | None] = None

    module: str = Field(default="", min_length=1)
    options: dict[str, Any] | None = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Process `module=` and `module_namespace=` class-keyword arguments.

        Only namespace resolution and validation happen here.  The actual
        Pydantic field specialization for `module` is deferred to
        `__pydantic_init_subclass__` so that it runs after Pydantic has
        finished building the model and all field defaults are in place.

        Args:
            **kwargs: Additional keyword arguments passed to parent classes.

        """
        module_namespace = kwargs.pop("module_namespace", None)
        module = kwargs.pop("module", None)
        super().__init_subclass__(**kwargs)
        if module_namespace is not None:
            cls._apply_module_namespace(module_namespace)
        if module is not None:
            module_full_name = cls._resolve_module_name(module)
            # Store for __pydantic_init_subclass__ to consume.
            cls._pending_module = module_full_name
            # Also set the class attribute so plain access works.
            cls.__annotations__ = {
                **getattr(cls, "__annotations__", {}),
                "module": Literal[module_full_name],
            }
        if inspect.isabstract(cls) or cls.__name__.endswith("ABC"):
            return
        # For non-pydantic paths (shouldn't exist anymore) validate at class time.
        if cls._pending_module is None:
            cls._validate_module_definition()

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:  # noqa: PLW3201
        """
        Finalize the `module` field specialization after Pydantic builds the model.

        This hook runs after Pydantic has completed model construction, so all
        field defaults inherited from parent classes are stable.

        Args:
            **kwargs: Additional keyword arguments passed to parent classes.

        """
        super().__pydantic_init_subclass__(**kwargs)
        pending = cls.__dict__.get("_pending_module")
        if pending is None:
            return
        field = cls.model_fields.get("module")
        if field is not None:
            field.annotation = cast("Any", Literal[pending])
            field.default = pending
            cls.model_rebuild(force=True)
        # Clear the pending marker so subclasses don't inherit it.
        cls._pending_module = None

    @classmethod
    def _apply_module_namespace(cls, module_namespace: str) -> None:
        """
        Store the `module_namespace=` class-keyword value as a class variable.

        Args:
            module_namespace: A bare flepimop2 namespace such as `"backend"`.

        Raises:
            TypeError: If the namespace conflicts with an explicit class-body
                `module_namespace` attribute or is not a non-empty string.

        """
        if "module_namespace" in cls.__dict__:
            msg = (
                f"Class '{cls.__name__}' cannot define both class attribute "
                "'module_namespace' and class keyword argument `module_namespace=`."
            )
            raise TypeError(msg)
        if not isinstance(module_namespace, str) or not module_namespace:
            msg = (
                f"Class '{cls.__name__}' must define class attribute "
                "'module_namespace' as a non-empty string."
            )
            raise TypeError(msg)
        cls.module_namespace = module_namespace

    @classmethod
    def _resolve_module_name(cls, module: str) -> str:
        """
        Resolve a short module name to a fully-qualified flepimop2 path.

        Also validates that the `module=` shortcut doesn't conflict with an
        explicit class-body `module` field declaration.

        Args:
            module: A short name or a fully-qualified path.

        Returns:
            The fully-qualified module path.

        Raises:
            TypeError: If the name is invalid, conflicts with an explicit
                class-body attribute, or a namespace cannot be inferred.

        """
        if "module" in cls.__dict__ and cls.__dict__.get("module") is not None:
            # A non-None concrete value in __dict__ means an explicit class
            # attribute - conflict with the keyword shortcut.
            existing = cls.__dict__["module"]
            if isinstance(existing, str) and existing:
                msg = (
                    f"Concrete class '{cls.__name__}' cannot define both class "
                    "attribute 'module' and class keyword argument `module=`."
                )
                raise TypeError(msg)
        if not isinstance(module, str) or not module:
            msg = (
                f"Concrete class '{cls.__name__}' must define class attribute "
                "'module' as a non-empty string."
            )
            raise TypeError(msg)
        if "." in module:
            return module
        if cls.module_namespace is None:
            msg = (
                f"Concrete class '{cls.__name__}' must define `module_namespace` to "
                "use the class keyword argument `module=` with a short module name. "
                "Use a fully-qualified module string or inherit from a namespaced "
                "ModuleBase subclass."
            )
            raise TypeError(msg)
        return f"flepimop2.{cls.module_namespace}.{module}"

    @classmethod
    def _validate_module_definition(cls) -> None:
        """
        Ensure a concrete subclass has resolved its `module` to a non-empty string.

        Checks the class's own `__dict__` for a direct string assignment or
        annotation default.  This runs during `__init_subclass__` before Pydantic
        has built `model_fields`, so we inspect the raw class namespace.

        Raises:
            TypeError: If `module` is missing or not a non-empty string.

        """
        # Direct class-body assignment (after shortcut resolution).
        module = cls.__dict__.get("module")
        if module is None:
            annotations = inspect.get_annotations(cls, eval_str=False)
            if "module" in annotations:
                return
        if not isinstance(module, str) or not module:
            msg = (
                f"Concrete class '{cls.__name__}' must define class attribute "
                "'module' as a non-empty string."
            )
            raise TypeError(msg)

    @classmethod
    def from_shorthand(cls, shorthand: str) -> Self:
        """
        Build an instance from shorthand configuration text.

        Concrete modules may override this optional hook to support
        configuration values shaped like `module_name(...)`.  The provided
        `shorthand` is the text inside the parentheses.

        Args:
            shorthand: The text contained within the shorthand parentheses.

        Raises:
            NotImplementedError: If the module does not support shorthand syntax.

        """
        msg = "Shorthand syntax is not supported by this module."
        raise NotImplementedError(msg)

    def option(self, name: str, default: Any = RaiseOnMissing) -> Any:  # noqa: ANN401
        """
        Retrieve an option value by name, with an optional default.

        Args:
            name: The name of the option to retrieve.
            default: The default value to return if the option is not found.
                Omitting this argument causes a `KeyError` when the option
                is missing.

        Returns:
            The value of the option if found, otherwise the default value.

        Raises:
            KeyError: If the option is missing and `default` is not provided.

        Examples:
            >>> from flepimop2.module import ModuleBase
            >>> class MyModule(ModuleBase, module="flepimop2.test.mymodule"):
            ...     pass
            >>> mod = MyModule.model_validate({"options": {"option1": 42}})
            >>> mod.option("option1")
            42
            >>> mod.option("option2", default="default_value")
            'default_value'
            >>> mod.option("option2")
            Traceback (most recent call last):
                ...
            KeyError: "Option 'option2' not found in module 'flepimop2.test.mymodule'."
            >>> class MyModuleWithMissingOption(
            ...     ModuleBase, module="flepimop2.test.noopts"
            ... ):
            ...     pass
            >>> mod = MyModuleWithMissingOption()
            >>> mod.option("option1", default="default_value")
            'default_value'
            >>> mod.option("option1")
            Traceback (most recent call last):
                ...
            KeyError: "Option 'option1' not found in module 'flepimop2.test.noopts'."

        """
        opts = self.options or {}
        if name not in opts and isinstance(default, RaiseOnMissingType):
            msg = f"Option '{name}' not found in module '{self.module}'."
            raise KeyError(msg)
        return opts.get(name, default)

    def to_yaml_data(self) -> object:
        """
        Convert the module configuration into YAML-ready Python objects.

        Subclasses can override this to customize just their serialized
        configuration block without changing patch semantics.

        Returns:
            A YAML-ready representation of the module configuration.
        """
        data = _model_to_yaml_mapping(self)
        if not data.get("options"):
            data.pop("options", None)
        return data

    def patch(
        self,
        other: Self,
        *,
        conflict: Literal[PatchConflictMode.MERGE, PatchConflictMode.REPLACE],
    ) -> Self:
        """
        Patch this module configuration with another module configuration.

        This method treats `other` as the incoming patch. The default
        implementation is intentionally simple: replace wholesale for `replace`,
        and deep-merge dumped model dictionaries for `merge`.

        Module developers can override this method to implement more complex patching
        logic if needed (e.g. merging certain subsections or sets of fields while
        replacing others). However, they should still try to respect the semantics of
        the `conflict` argument as much as possible to avoid surprising users.

        Args:
            other: The patch to apply to this module.
            conflict: How to handle overlapping fields.

        Returns:
            The patched module configuration.

        Raises:
            TypeError: If `self` and `other` are different concrete model types.
        """
        if type(self) is not type(other):
            msg = (
                f"Cannot patch {type(self).__name__} with {type(other).__name__}; "
                "module patching requires matching concrete types."
            )
            raise TypeError(msg)
        if conflict is PatchConflictMode.REPLACE:
            return other.model_copy(deep=True)
        return type(self).model_validate(
            _deep_merge_dicts(self.model_dump(), other.model_dump())
        )
