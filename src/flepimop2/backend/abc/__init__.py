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
"""Abstract base class for flepimop2 file IO backends."""

__all__ = ["BackendABC", "build"]

from abc import abstractmethod
from typing import Any

from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel
from flepimop2.meta import RunMeta
from flepimop2.module import ModuleABC
from flepimop2.typing import Float64NDArray


class BackendABC(ModuleABC):
    """Abstract base class for flepimop2 file IO backends."""

    def save(self, data: Float64NDArray, run_meta: RunMeta) -> None:
        """
        Save a numpy array to storage.

        Args:
            data: The numpy array to save.
            run_meta: Metadata about the current run.
        """
        return self._save(data, run_meta)

    def read(self, run_meta: RunMeta) -> Float64NDArray:
        """
        Read a numpy array from storage.

        Args:
            run_meta: Metadata about the current run.

        Returns:
            The numpy array read from storage.
        """
        return self._read(run_meta)

    @abstractmethod
    def _save(self, data: Float64NDArray, run_meta: RunMeta) -> None:
        """Backend-specific implementation for saving data."""
        ...

    @abstractmethod
    def _read(self, run_meta: RunMeta) -> Float64NDArray:
        """Backend-specific implementation for reading data."""
        ...


def build(config: dict[str, Any] | ModuleModel) -> BackendABC:
    """Build a `BackendABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary. The dict must contains a 'module' key, which
            will be used to lookup the Backend module path. The module will have
            "flepimop2.backend." prepended.

    Returns:
        The constructed backend instance.

    """
    return _build(config, "backend", "flepimop2.backend.csv", BackendABC)
