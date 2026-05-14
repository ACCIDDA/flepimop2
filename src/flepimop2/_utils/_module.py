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
"""Private utilities for dynamic module loading and validation."""

import inspect
import re
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from os import PathLike
from pathlib import Path
from types import ModuleType
from typing import (
    Any,
    Literal,
    NamedTuple,
    Self,
    TypeVar,
)

from pydantic import TypeAdapter, ValidationError

from flepimop2.module import ModuleBase
from flepimop2.typing import IdentifierString

Namespace = Literal["backend", "engine", "parameter", "process", "scenario", "system"]

T = TypeVar("T", bound=ModuleBase)
SHORTHAND_PATTERN = re.compile(
    r"^\s*(?P<module>[A-Za-z_][A-Za-z0-9_\.]*)\((?P<args>.*)\)\s*$",
    re.DOTALL,
)
IDENTIFIER_STRING_ADAPTER = TypeAdapter(IdentifierString)


class ParsedShorthand(NamedTuple):
    """
    Parsed representation of shorthand module configuration text.

    This class represents the result of parsing a shorthand configuration string, i.e.
    `from: ...`. It contains the extracted module token and the argument payload as
    separate attributes. For example, parsing the string `fixed(0.3)` would yield a
    `ParsedShorthand` with `module='fixed'` and `args='0.3'`.

    Attributes:
        module: The module token extracted from the shorthand text.
        args: The argument payload extracted from the shorthand text.
    """

    module: IdentifierString
    args: str

    @classmethod
    def from_string(cls, value: str) -> Self:
        r"""
        Parse shorthand config text into a module token and argument payload.

        Args:
            value: Shorthand configuration text such as `fixed(0.3)`.

        Returns:
            A parsed shorthand object containing the module token and argument
            payload.

        Raises:
            ValueError: If the text does not match shorthand syntax.

        Examples:
            >>> from flepimop2._utils._module import ParsedShorthand
            >>> ParsedShorthand.from_string("fixed(0.3)")
            ParsedShorthand(module='fixed', args='0.3')
            >>> ParsedShorthand.from_string(" normal(-1, 2.5) ")
            ParsedShorthand(module='normal', args='-1, 2.5')
            >>> parsed = ParsedShorthand.from_string('''fixed(
            ...   3.1415
            ... )''')
            >>> parsed.module
            'fixed'
            >>> parsed.args == '''
            ...   3.1415
            ... '''
            True
            >>> try:
            ...     ParsedShorthand.from_string("Normal(1)")
            ... except ValueError as exc:
            ...     print(exc)
            Shorthand module name 'Normal' must satisfy IdentifierString.
            >>> try:
            ...     ParsedShorthand.from_string("fixed")
            ... except ValueError as exc:
            ...     print(exc)
            Shorthand module configuration must match the form 'module_name(...)'.
        """
        match = SHORTHAND_PATTERN.fullmatch(value)
        if match is None:
            msg = (
                "Shorthand module configuration must match the form 'module_name(...)'."
            )
            raise ValueError(msg)
        raw_module = match.group("module")
        try:
            module = IDENTIFIER_STRING_ADAPTER.validate_python(raw_module)
        except ValidationError as exc:
            msg = f"Shorthand module name {raw_module!r} must satisfy IdentifierString."
            raise ValueError(msg) from exc
        return cls(
            module=module,
            args=match.group("args"),
        )


def _as_dict(
    config: dict[IdentifierString, Any] | ModuleBase | None = None,
) -> dict[IdentifierString, Any]:
    """
    Ensure a Model can be used as a dictionary.

    Args:
        config: The configuration to potentially convert.

    Returns:
        A dictionary representation of the configuration.

    Raises:
        TypeError: If the config is not a dictionary, ModuleBase, or None.
    """
    if config is None:
        return {}
    if isinstance(config, ModuleBase):
        return config.model_dump()
    if isinstance(config, dict):
        return config.copy()
    msg = f"Expected config to be a dict or ModuleBase, got {type(config).__name__}"
    raise TypeError(msg)


def _load_module(path: PathLike[str], mod_name: str) -> ModuleType:
    """
    Load a Python module from a given file path as a given name.

    Args:
        path: The path to the Python file.
        mod_name: The name of the module to load.

    Returns:
        The loaded module.

    Raises:
        FileNotFoundError: If the file does not exist.
        FileNotFoundError: If the file is not a valid Python file.
        ImportError: If the module could not be loaded.

    """
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        msg = f"No file found at: {resolved}"
        raise FileNotFoundError(msg)
    if resolved.suffix != ".py":
        msg = f"No valid Python file found at: {resolved}"
        raise FileNotFoundError(msg)
    spec = spec_from_file_location(mod_name, str(resolved))
    if not (spec and spec.loader):
        msg = f"Could not load module from spec at: {resolved}"
        raise ImportError(msg)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_function(module: ModuleType, func_name: str) -> bool:
    """
    Check if a module has a callable function with the given name.

    Args:
        module: The module to check.
        func_name: The name of the function to check for.

    Returns:
        `True` if the module has a callable function with the given name,
        `False` otherwise.
    """
    return hasattr(module, func_name) and callable(getattr(module, func_name))


def _find_module_class(
    mod: ModuleType,
    mod_name: str,
    enforced_type: type[T],
) -> type[T]:
    """
    Find a `ModuleBase` subclass defined directly in a module.

    Args:
        mod: The module to search.
        mod_name: The fully qualified module name (used to filter classes to
            those defined in this module, not imported ones).
        enforced_type: The ABC type the class must satisfy.

    Returns:
        The matching `ModuleBase` subclass.

    Raises:
        AttributeError: If no valid class is found.

    """
    for _, obj in inspect.getmembers(mod, inspect.isclass):
        if obj.__module__ != mod_name:
            continue
        try:
            if issubclass(obj, enforced_type) and issubclass(obj, ModuleBase):
                return obj
        except TypeError:
            continue
    msg = (
        f"Module '{mod_name}' does not define a {enforced_type.__name__} subclass "
        "that inherits from ModuleBase."
    )
    raise AttributeError(msg)


def _resolve_module_name(module: str, namespace: Namespace) -> str:
    """
    Resolve a module name, optionally prefixing it with a namespace.

    If the provided module name already contains a dot (i.e., is fully qualified),
    it is returned unchanged. Otherwise, the given namespace is prepended.

    Args:
        module: The module name to resolve.
        namespace: The namespace to prepend if the module name is not fully qualified.

    Returns:
        The fully qualified module name.

    Examples:
        >>> from flepimop2._utils._module import _resolve_module_name
        >>> _resolve_module_name("my_parquet_backend", "backend")
        'flepimop2.backend.my_parquet_backend'
        >>> _resolve_module_name("my_stochastic_solver", "engine")
        'flepimop2.engine.my_stochastic_solver'
        >>> _resolve_module_name("external.sde_model_builder", "system")
        'external.sde_model_builder'

    """
    return module if "." in module else f"flepimop2.{namespace}.{module}"


def _build(
    config: dict[str, Any] | ModuleBase | str,
    namespace: Namespace,
    enforced_type: type[T],
) -> T:
    """
    Build an instance from a configuration dictionary.

    This is a consolidated builder function used by backend, engine, process, and
    system ABC build functions to reduce code duplication.

    Args:
        config: Configuration dictionary, `ModuleBase` instance, or shorthand text.
        namespace: The namespace for module resolution.
        enforced_type: The expected type of the built instance.

    Returns:
        The constructed instance.

    Raises:
        ValueError: If the configuration does not define a module.
        TypeError: If the built instance does not match the enforced type.

    """
    if isinstance(config, str):
        parsed = ParsedShorthand.from_string(config)
        module_path = _resolve_module_name(parsed.module, namespace)
        mod = import_module(module_path)
        target_class = _find_module_class(mod, module_path, enforced_type)
        try:
            instance = target_class.from_shorthand(parsed.args)
        except NotImplementedError as exc:
            msg = f"Module '{module_path}' does not support shorthand configuration."
            raise ValueError(msg) from exc
    else:
        config_dict = _as_dict(config)
        configured_module = config_dict.get("module")
        if not isinstance(configured_module, str) or not configured_module:
            msg = (
                f"Configuration for namespace '{namespace}' must define a non-empty "
                "'module' string."
            )
            raise ValueError(msg)
        module_path = _resolve_module_name(configured_module, namespace)
        config_dict["module"] = module_path

        mod = import_module(module_path)
        target_class = _find_module_class(mod, module_path, enforced_type)
        instance = target_class.model_validate(config_dict)

    if not isinstance(instance, enforced_type):
        msg = f"Built {type(instance)}, expected {enforced_type}"
        raise TypeError(msg)

    return instance
