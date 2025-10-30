from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from os import PathLike
from pathlib import Path
from types import ModuleType


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
