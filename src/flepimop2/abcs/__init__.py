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
    "ParameterABC",
    "ProcessABC",
    "SystemABC",
    "SystemProtocol",
]

from flepimop2.backend.abc import BackendABC
from flepimop2.engine.abc import EngineABC, EngineProtocol
from flepimop2.parameter.abc import ParameterABC
from flepimop2.process.abc import ProcessABC
from flepimop2.system.abc import SystemABC
from flepimop2.typing import SystemProtocol
