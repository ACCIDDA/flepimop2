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

__all__ = ["ModuleABC"]

import inspect
from abc import ABC
from typing import Any, ClassVar, Literal, Self

from flepimop2.typing import RaiseOnMissing, RaiseOnMissingType


class ModuleABC(ABC):
    """
    Abstract base class for flepimop2 modules.

    Attributes:
        module: The fully-qualified module name. Concrete subclasses may define
            this explicitly or provide a namespaced class keyword argument such as
            `module="csv"`.
        module_namespace: The flepimop2 namespace used to resolve short module
            names such as `"csv"` into fully-qualified paths.
        options: Optional dictionary of additional options the module exposes for
            `flepimop2` to take advantage of.

    """

    module_namespace: ClassVar[str | None] = None
    module: str
    options: dict[str, Any] | None = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Ensure concrete subclasses define a valid module name.

        This validation works for both plain Python and Pydantic-based subclasses.
        If `module_namespace="..."` or `module="..."` are supplied in the class
        definition, they are normalized before validation.

        Args:
            **kwargs: Additional keyword arguments passed to parent classes.

        """
        module_namespace = kwargs.pop("module_namespace", None)
        module = kwargs.pop("module", None)
        super().__init_subclass__(**kwargs)
        if module_namespace is not None:
            cls._apply_module_namespace(module_namespace)
        if module is not None:
            cls._apply_module_shortcut(module)
        if inspect.isabstract(cls) or cls.__name__.endswith("ABC"):
            return
        cls._validate_module_definition()

    @classmethod
    def _apply_module_namespace(cls, module_namespace: str) -> None:
        """
        Normalize the class-definition `module_namespace=` keyword argument.

        Args:
            module_namespace: A bare flepimop2 module namespace such as
                `"backend"` or `"system"`.

        Raises:
            TypeError: If the namespace is invalid or conflicts with an explicit
                `module_namespace` attribute defined in the class body.

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
    def _apply_module_shortcut(cls, module: str) -> None:
        """
        Normalize the class-definition `module=` shortcut into a full module path.

        Args:
            module: A short module name such as "csv" or a fully-qualified path.

        Raises:
            TypeError: If the shortcut is invalid or conflicts with an explicit
                `module` attribute defined in the class body.

        """
        if "module" in cls.__dict__:
            msg = (
                f"Concrete class '{cls.__name__}' cannot define both class attribute "
                "'module' and class keyword argument `module=`."
            )
            raise TypeError(msg)
        module_full_name = cls._resolve_module_name(module)
        cls.module = module_full_name
        cls.__annotations__ = {
            **getattr(cls, "__annotations__", {}),
            "module": Literal[module_full_name],
        }

    @classmethod
    def _resolve_module_name(cls, module: str) -> str:
        """
        Resolve a module shortcut into a fully-qualified flepimop2 module path.

        Args:
            module: A short module name or a fully-qualified module path.

        Returns:
            The fully-qualified module path.

        Raises:
            TypeError: If the module name is invalid or the namespace cannot be
                inferred from the subclass hierarchy.

        """
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
                "ModuleABC subclass."
            )
            raise TypeError(msg)
        return f"flepimop2.{cls.module_namespace}.{module}"

    @classmethod
    def _validate_module_definition(cls) -> None:
        """
        Ensure a concrete subclass defines a valid module name.

        Raises:
            TypeError: If the subclass does not define `module` as a non-empty string.

        """
        module = cls.__dict__.get("module")
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

        Concrete modules may override this optional hook to support configuration
        values shaped like `module_name(...)`. The provided `shorthand` is the text
        inside the parentheses.

        Args:
            shorthand: The text contained within the shorthand parentheses.

        Notes:
            This hook is primarily intended for external module providers that want
            to offer a concise string syntax for simple configurations.

            Before implementing shorthand, consider whether the module actually
            benefits from it. Modules that require many settings, nested structure,
            or richer validation are often better served by full YAML mappings than
            by a single string.

            Implementations should parse `shorthand` robustly. In particular,
            callers may supply multiline values from YAML block scalars, so parsing
            should tolerate embedded newlines and surrounding whitespace where that
            makes sense for the module's syntax.

            Implementations should raise `ValueError` for invalid shorthand input so
            users receive a clear configuration error rather than a generic failure.

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
            default: The default value to return if the option is not found. If
                not provided, defaults to `RaiseOnMissing`, which will cause a
                `KeyError` to be raised if the option is missing.

        Returns:
            The value of the option if found, otherwise the default value.

        Raises:
            KeyError: If the option is missing and `default` is not provided.

        Examples:
            >>> from flepimop2.module import ModuleABC
            >>> class MyModule(ModuleABC):
            ...     module = "my_module"
            ...     options = {"option1": 42}
            >>> mod = MyModule()
            >>> mod.option("option1")
            42
            >>> mod.option("option2", default="default_value")
            'default_value'
            >>> mod.option("option2")
            Traceback (most recent call last):
                ...
            KeyError: "Option 'option2' not found in module 'my_module'."
            >>> class MyModuleWithMissingOption(ModuleABC):
            ...     module = "missing_opts"
            >>> mod = MyModuleWithMissingOption()
            >>> mod.option("option1", default="default_value")
            'default_value'
            >>> mod.option("option1")
            Traceback (most recent call last):
                ...
            KeyError: "Option 'option1' not found in module 'missing_opts'."

        """
        opts = self.options or {}
        if name not in opts and isinstance(default, RaiseOnMissingType):
            msg = f"Option '{name}' not found in module '{self.module}'."
            raise KeyError(msg)
        return opts.get(name, default)
