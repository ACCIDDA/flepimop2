"""flepimop2 modeling pipeline package."""

from pkgutil import extend_path

__all__ = ["__version__", "backend", "configuration", "logging"]

__path__ = extend_path(__path__, __name__)
__version__ = "0.1.0"

from flepimop2 import backend, configuration, logging
