"""Abstract base class for flepimop2 file IO backends."""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from numpy.typing import NDArray

from flepimop2._utils import _load_builder
from flepimop2.meta import RunMeta


class BackendABC(ABC):
    """Abstract base class for flepimop2 file IO backends."""

    def __init__(self, backend_model: dict[str, Any]) -> None:  # noqa: B027
        """
        Initialize the backend with the given configuration.

        Args:
            backend_model: The configuration dictionary for the backend.
        """

    def save(self, data: NDArray[np.float64], run_meta: RunMeta) -> None:
        """
        Save a numpy array to storage.

        Args:
            data: The numpy array to save.
            run_meta: Metadata about the current run.
        """
        return self._save(data, run_meta)

    def read(self, run_meta: RunMeta) -> NDArray[np.float64]:
        """
        Read a numpy array from storage.

        Args:
            run_meta: Metadata about the current run.

        Returns:
            The numpy array read from storage.
        """
        return self._read(run_meta)

    @abstractmethod
    def _save(self, data: NDArray[np.float64], run_meta: RunMeta) -> None:
        """Backend-specific implementation for saving data."""
        ...

    @abstractmethod
    def _read(self, run_meta: RunMeta) -> NDArray[np.float64]:
        """Backend-specific implementation for reading data."""
        ...


def build(config: dict[str, Any]) -> BackendABC:
    """Build a `BackendABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary. The dict must contains a 'module' key, which
            will be used to lookup the Backend module path. The module will have
            "flepimop2.backend." prepended.

    Returns:
        The constructed backend instance.

    Raises:
        TypeError: If the built backend is not an instance of BackendABC.
    """
    builder = _load_builder(f"flepimop2.backend.{config.pop('module', 'csv')}")
    backend = builder.build(**config)
    if not isinstance(backend, BackendABC):
        msg = "The built backend is not an instance of BackendABC."
        raise TypeError(msg)
    return backend
