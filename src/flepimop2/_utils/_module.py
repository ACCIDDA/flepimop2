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
    module_name: str, component: Literal["backend", "engine", "process", "system"]
) -> str:
    """
    Resolve a module name that may omit the full namespace.

    Args:
        module_name: The configured module name (possibly short).
        component: The component type (e.g., "backend", "engine", etc.).

    Returns:
        The fully qualified module name.

    Examples:
        >>> from flepimop2._utils._module import _resolve_module_name
        >>> _resolve_module_name("s3", "backend")
        'flepimop2.backend.s3_backend'
        >>> _resolve_module_name("custom_pkg.custom_module", "process")
        'custom_pkg.custom_module'

    """
    if "." in module_name:
        return module_name
    return f"flepimop2.{component}.{module_name}_{component}"
