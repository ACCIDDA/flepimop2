"""Private utilities for dynamic module loading and validation."""

import inspect
from abc import ABCMeta
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from os import PathLike
from pathlib import Path
from types import ModuleType
from typing import Any, Literal, Protocol, TypeVar, cast, runtime_checkable

from pydantic import BaseModel

from flepimop2.configuration import ModuleModel
from flepimop2.module import ModuleABC
from flepimop2.typing import IdentifierString

Namespace = Literal["backend", "engine", "parameter", "process", "system"]

T_co = TypeVar("T_co", bound=ModuleABC, covariant=True)


@runtime_checkable
class Buildable(Protocol[T_co]):
    """
    Protocol for modules that can be built from a configuration.

    This protocol defines the expected interface for modules that can be built using
    the `_build` function. It requires a `build` method that takes a configuration
    dictionary or a `ModuleModel` instance and returns an instance of type `T`.

    Attributes:
        build: A callable that constructs an instance of type `T` from a
        configuration.

    """

    def build(self, config: dict[Any, Any] | ModuleModel) -> T_co: ...


def _as_dict(
    config: dict[IdentifierString, Any] | ModuleModel | None = None,
) -> dict[IdentifierString, Any]:
    """
    Ensure a Model can be used as a dictionary.

    Args:
        config: The configuration to potentially convert.

    Returns:
        A dictionary representation of the configuration.

    Raises:
        TypeError: If the config is not a dictionary, ModuleModel, or None.
    """
    if config is None:
        return {}
    if isinstance(config, ModuleModel):
        return config.model_dump()
    if isinstance(config, dict):
        return config.copy()

    msg = f"Expected config to be a dict or ModuleModel, got {type(config).__name__}"
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


def _load_builder(
    mod_name: str, _enforced_type: type[T_co] | ABCMeta
) -> Buildable[T_co]:
    """
    Load a Python module from a given file path as a given name.

    Args:
        mod_name: The name of the module to load.
        _enforced_type: The type that the loaded module must enforce.

    Returns:
        The loaded module.

    Raises:
        AttributeError: If the module does not have a 'build' function or a valid
            BaseModel for default building.

    """
    mod = import_module(mod_name)

    # Check if module already satisfies the protocol
    if isinstance(mod, Buildable):
        # We cast because runtime check doesn't guarantee the internal T_co
        return cast("Buildable[T_co]", mod)

    target_class = _find_target_class(mod, mod_name)
    if target_class is None:
        msg = f"Module '{mod_name}' lacks a 'build' function or valid BaseModel."
        raise AttributeError(msg)

    # We define the internal function. Note that 'target_class'
    # needs to be cast to T_co since we're promising the caller a T_co.
    def dynamic_build(config: dict[IdentifierString, Any] | ModuleModel) -> T_co:
        # Validate returns an instance of the class; we cast it to the expected T_co
        return cast("T_co", target_class.model_validate(_as_dict(config)))

    setattr(mod, "build", dynamic_build)
    return cast("Buildable[T_co]", mod)


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
    enforced_type: type[T_co] | ABCMeta,
) -> T_co:
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
        TypeError: If the built instance does not match the enforced type.

    """
    config_dict = _as_dict(config)
    if "module" not in config_dict:
        config_dict["module"] = default_module
    module_path = _resolve_module_name(config_dict["module"], namespace)
    config_dict["module"] = module_path

    # Anchor T_co by passing enforced_type
    builder: Buildable[T_co] = _load_builder(module_path, enforced_type)

    instance = builder.build(config_dict)

    # Final runtime safety check since we've done a lot of casting
    if not isinstance(instance, enforced_type):
        msg = f"Built {type(instance)}, expected {enforced_type}"
        raise TypeError(msg)

    return instance
