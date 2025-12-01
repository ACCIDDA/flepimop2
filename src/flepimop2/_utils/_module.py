"""Private utilities for dynamic module loading and validation."""

import inspect
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from os import PathLike
from pathlib import Path
from types import ModuleType
from typing import Any, Literal, TypeVar

from pydantic import BaseModel

from flepimop2.configuration import ModuleModel

T = TypeVar("T")
Namespace = Literal["backend", "engine", "process", "system"]


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


def _find_target_class(mod: ModuleType, mod_name: str) -> type[BaseModel] | None:
    """
    Find a BaseModel subclass defined in a module.

    This function finds a target class in a module that is able to support a default
    build function. The criteria for the target class is that it must be a subclass
    of `pydantic.BaseModel` (excluding `BaseModel` itself and `ModuleModel`) and must
    be defined within the module itself.

    Args:
        mod: The module to search.
        mod_name: The fully qualified module name.

    Returns:
        The target BaseModel subclass if found, None otherwise.

    """
    possible_objs = [
        obj
        for _, obj in inspect.getmembers(mod, inspect.isclass)
        if obj not in {BaseModel, ModuleModel} and obj.__module__ == mod_name
    ]
    for obj in possible_objs:
        try:
            if issubclass(obj, BaseModel):
                return obj
        except TypeError:
            continue
    return None


def _load_builder(mod_name: str) -> ModuleType:
    """
    Load a module and ensure it has a valid build function.

    Args:
        mod_name: The fully qualified module name to load.

    Returns:
        The loaded module.

    Raises:
        AttributeError: If the module does not have a valid build function.

    Notes:
        A valid build function is either defined directly in the module,
        or can be dynamically created if the module contains a target
        class that supports a default build function.

    """
    # Try to import a build function directly
    # and return the module if found
    mod = import_module(mod_name)
    if _validate_function(mod, "build"):
        return mod

    # If a build function is not found see if the target
    # class can be loaded with a default build function
    target_class = _find_target_class(mod, mod_name)
    if target_class is None:
        msg = f"Module '{mod_name}' does not have a valid 'build' function."
        raise AttributeError(msg)

    # If the target class supports a default build function,
    # dynamically add it to the module and return it
    def build(config: dict[str, Any] | ModuleModel) -> BaseModel:
        return target_class.model_validate(
            config.model_dump() if isinstance(config, ModuleModel) else config
        )

    mod.build = build  # type: ignore[attr-defined]
    return mod


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
    config: dict[str, Any] | ModuleModel,
    namespace: Namespace,
    default_module: str,
    enforced_type: type[T],
) -> T:
    """
    Build an instance from a configuration dictionary.

    This is a consolidated builder function used by backend, engine, process, and
    system ABC build functions to reduce code duplication.

    Args:
        config: Configuration dictionary or `ModuleModel` instance.
        namespace: The namespace for module resolution.
        default_module: The default module to use if not specified in config.
        enforced_type: The expected type of the built instance. Can be an abstract
            class since it's only used for isinstance checks, not instantiation.

    Returns:
        The constructed instance.

    Raises:
        TypeError: If the built instance is not of the expected type.
    """
    config_dict = {"module": default_module} | (
        config.model_dump() if isinstance(config, ModuleModel) else config
    )
    module = _resolve_module_name(config_dict["module"], namespace)
    config_dict["module"] = module
    builder = _load_builder(module)
    instance = builder.build(config_dict)
    if not isinstance(instance, enforced_type):
        msg = f"The built instance is not an instance of {enforced_type.__name__}."
        raise TypeError(msg)
    return instance
