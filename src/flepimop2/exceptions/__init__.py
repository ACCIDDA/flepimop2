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
"""Custom exceptions provided by the `flepimop2` package."""

__all__ = [
    "Flepimop2Error",
    "Flepimop2ValidationError",
    "ValidationIssue",
]

from flepimop2.exceptions._flepimop2_error import Flepimop2Error
from flepimop2.exceptions._flepimop2_validation_error import (
    Flepimop2ValidationError,
    ValidationIssue,
)
