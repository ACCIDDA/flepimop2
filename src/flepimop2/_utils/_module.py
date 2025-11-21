from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from os import PathLike
from pathlib import Path
from types import ModuleType
from typing import Literal


def _load_module(path: PathLike[str], mod_name: str) -> ModuleType:
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
    return hasattr(module, func_name) and callable(getattr(module, func_name))


def _load_builder(mod_name: str) -> ModuleType:
    mod = import_module(mod_name)
    if _validate_function(mod, "build"):
        return mod
    msg = f"Module '{mod_name}' does not have a valid 'build' function."
    raise AttributeError(msg)


def _resolve_module_name(
    module: str, namespace: Literal["backend", "engine", "process", "system"]
) -> str:
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
