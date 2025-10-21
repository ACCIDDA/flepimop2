from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from flepimop2.backends._backend import BackendABC
from flepimop2.meta import RunMeta


class CsvBackend(BackendABC):
    """CSV backend for saving numpy arrays to CSV files."""

    def __init__(self, backend_model: dict[str, Any]) -> None:
        """
        Initialize the CSV backend with configuration.

        Args:
            backend_model: Configuration dictionary from BackendModel.model_dump().
                Expected to contain a 'path' key with the base output directory.

        Raises:
            TypeError: If the 'path' in `backend_model` is not a string or Path.
        """
        base_path = backend_model.get("path", Path.cwd() / "model_output")
        if not isinstance(base_path, str | Path):
            msg = "The 'path' in backend configuration must be a string or Path."
            raise TypeError(msg)
        self.base_path = Path(base_path)

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
