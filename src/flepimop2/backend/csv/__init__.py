"""CSV backend for flepimop2."""

import os
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import Field, field_validator

from flepimop2.backend.abc import BackendABC
from flepimop2.configuration import ModuleModel
from flepimop2.meta import RunMeta


class CsvBackend(ModuleModel, BackendABC):
    """CSV backend for saving numpy arrays to CSV files."""

    module: Literal["flepimop2.backend.csv"] = "flepimop2.backend.csv"
    root: Path = Field(default_factory=lambda: Path.cwd() / "model_output")

    @field_validator("root", mode="after")
    @classmethod
    def _validate_root(cls, root: Path) -> Path:
        """
        Validate that the root path is a writable directory.

        Args:
            root: The root path to validate.

        Returns:
            The validated root path.

        Raises:
            TypeError: If the root path is not a directory or is not writable.
        """
        if not (root.is_dir() and os.access(root, os.W_OK)):
            msg = f"The specified 'root' is not a directory or is not writable: {root}"
            raise TypeError(msg)
        return root

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
        return self.root / filename

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
