"""Base class for defining modules in the system, engine, or backend."""

__all__ = ["ModuleABC"]

import inspect
from abc import ABC
from typing import Any

from flepimop2.typing import RaiseOnMissing, RaiseOnMissingType


class ModuleABC(ABC):
    """
    Abstract base class for modules in the system, engine, or backend.

    Attributes:
        module: The name of the module.
        options: Optional dictionary of additional options the module exposes for
            `flepimop2` to take advantage of.

    """

    module: str
    options: dict[str, Any] | None = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Ensure concrete subclasses define a valid module name.

        This validation works for both plain Python and Pydantic-based subclasses.

        Args:
            **kwargs: Additional keyword arguments passed to parent classes.

        Raises:
            TypeError: If a concrete subclass does not define a valid `module` string.

        """
        super().__init_subclass__(**kwargs)
        if inspect.isabstract(cls) or cls.__name__.endswith("ABC"):
            return
        module = cls.__dict__.get("module")
        if not isinstance(module, str) or not module:
            msg = (
                f"Concrete class '{cls.__name__}' must define class attribute "
                "'module' as a non-empty string."
            )
            raise TypeError(msg)

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
