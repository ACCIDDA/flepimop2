"""
Abstract base classes for flepimop2 modules.

This module provides abstract base classes (ABCs) for key modules of the flepimop2
pipeline. The ABCs defined here can also be found in their respective submodules, but
are re-exported here for developer convenience.

"""

__all__ = [
    "BackendABC",
    "EngineABC",
    "EngineProtocol",
    "ProcessABC",
    "SystemABC",
    "SystemProtocol",
]

from flepimop2.backend.abc import BackendABC
from flepimop2.engine.abc import EngineABC, EngineProtocol
from flepimop2.process.abc import ProcessABC
from flepimop2.system.abc import SystemABC, SystemProtocol
