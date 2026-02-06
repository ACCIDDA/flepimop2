"""
Custom Typing Helpers.

This module centralizes type aliases used throughout the project and makes
it easy to keep runtime imports lightweight while still providing precise
type information. The goal is to express common shapes and dtypes once,
so internal modules can share consistent, readable annotations without
repeating NumPy typing boilerplate.

Examples:
    >>> from flepimop2.typing import Float64NDArray
    >>> Float64NDArray
    numpy.ndarray[tuple[typing.Any, ...], numpy.dtype[numpy.float64]]
"""

__all__ = ["Float64NDArray"]

import numpy as np
import numpy.typing as npt

Float64NDArray = npt.NDArray[np.float64]
"""Alias for a NumPy ndarray with float64 data type."""
