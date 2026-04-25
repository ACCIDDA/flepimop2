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
"""Representations of parsed configuration files."""

__all__ = [
    "AxesGroupModel",
    "AxisModel",
    "CategoricalAxisModel",
    "ConfigurationModel",
    "ContinuousAxisModel",
    "ModuleGroupModel",
    "ModuleModel",
    "SimulateSpecificationModel",
]

from flepimop2.configuration._axes import (
    AxesGroupModel,
    AxisModel,
    CategoricalAxisModel,
    ContinuousAxisModel,
)
from flepimop2.configuration._configuration import ConfigurationModel
from flepimop2.configuration._module import ModuleGroupModel, ModuleModel
from flepimop2.configuration._simulate import SimulateSpecificationModel
