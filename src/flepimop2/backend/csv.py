"""CSV backend for flepimop2."""

import os
from os import PathLike
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from flepimop2.backend.abc import BackendABC
from flepimop2.meta import RunMeta


class CsvBackend(BackendABC):
    """CSV backend for saving numpy arrays to CSV files."""

    def __init__(self, root: PathLike[str] | None) -> None:
        """
        Initialize the CSV backend with configuration.

        Args:
            root: Base output directory for CSV files.

        Raises:
            TypeError: If the 'root' is not a string or Path.
        """
        base_path = Path(root) if root is not None else Path.cwd() / "model_output"
        if base_path.is_file():
            msg = "The 'path' in backend configuration must be a directory."
            raise TypeError(msg)
        if not (base_path.exists() and os.access(base_path, os.W_OK)):
            msg = f"The specified 'path' does not exist or is not writable: {base_path}"
            raise TypeError(msg)
        self.base_path = base_path

    def _get_file_path(self, run_meta: RunMeta) -> Path:
        """
        Generate a dynamic file path based on run metadata.

        Args:
            run_meta: Metadata about the current run.

        Returns:
            The dynamically generated file path.
        """
        timestamp_str = run_meta.timestamp.strftime("%Y%m%d_%H%M%S")
        name_part = f"{run_meta.name}_" if run_meta.name else ""
        filename = f"{name_part}{run_meta.action}_{timestamp_str}.csv"
        return self.base_path / filename

    def _save(self, data: NDArray[np.float64], run_meta: RunMeta) -> None:
        """
        Save a numpy array to a CSV file.

        Args:
            data: The numpy array to save.
            run_meta: Metadata about the current run.
        """
        file_path = self._get_file_path(run_meta)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        np.savetxt(file_path, data, delimiter=",")

    def _read(self, run_meta: RunMeta) -> NDArray[np.float64]:
        """
        Read a numpy array from a CSV file.

        Args:
            run_meta: Metadata about the current run.

        Returns:
            The numpy array read from the CSV file.
        """
        file_path = self._get_file_path(run_meta)
        return np.loadtxt(file_path, delimiter=",")


def build(root: PathLike[str] | None = None) -> BackendABC:
    """
    Build a `CsvBackend` from a configuration dictionary.

    Args:
        root: Base output directory for CSV files. 'module' key, which will be used to
            lookup the Backend module path. The module will have "flepimop2.backends."
            prepended.

    Returns:
        The constructed csv backend.
    """
    return CsvBackend(root)
