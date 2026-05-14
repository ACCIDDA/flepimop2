<!-- skip: start -->
# Creating an External Provider Package

This tutorial will show how to:

- Create an external provider package that extends `flepimop2` functionality.
- Structure the package as a PEP 420 implicit namespace package.
- Implement a custom backend module class.
- Use the external provider package in a `flepimop2` configuration file.
- Appropriately license external provider packages.

In this tutorial, we will create a new backend package called `flepimop2-npz-backend` that provides an `NpzBackend` class for saving and loading NumPy arrays using the `.npz` format.

## What is an External Provider Package?

An external provider package allows users to extend `flepimop2` with custom implementations of systems, engines, backends, or processors without modifying the core `flepimop2` codebase. This is particularly useful for:

- Domain-specific models or algorithms.
- Custom file formats or storage backends.
- Specialized processing pipelines.
- Experimental features that may not be suitable for the core library.

External provider packages leverage Python's namespace package mechanism to seamlessly integrate with `flepimop2`'s module resolution system.

## Brief Overview of Namespace Packages

`flepimop2` uses [PEP 420 implicit namespace packages](https://peps.python.org/pep-0420/) to allow external packages to contribute modules that can be referenced directly in configuration files. This means:

- External packages can add modules under the `flepimop2.*` namespace without conflicts.
- Users can reference modules by short names (e.g., `module: 'npz'`) instead of full paths.
- `flepimop2` automatically resolves `module: 'npz'` to `flepimop2.backend.npz` when loading backend configurations.

The key to making this work is:

1. **No `__init__.py` files** in the namespace directories (e.g., `src/flepimop2/`, `src/flepimop2/backend/`)
2. Proper configuration in `pyproject.toml` to tell the build system where to find the namespace packages
3. Only the leaf module directory (e.g., `src/flepimop2/backend/npz/`) should have an `__init__.py` file

For more details, see the [Python Packaging Guide on Namespace Packages](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/).

## Creating the External Provider Package

### Step 1: Initialize the Package with `uv`

First, create a new Python package using `uv` with the `hatch` build backend:

```bash
# Create a new directory for your package
mkdir flepimop2-npz-backend
cd flepimop2-npz-backend

# Initialize a new Python package
uv init --package --build-backend hatchling

# Add dependencies
uv add numpy
uv add "flepimop2~=0.0"
```

This creates a basic package structure with a `pyproject.toml` file configured to use the Hatch build backend.

`flepimop2` is still in its pre-1.0 release line, so provider packages should pin to the current major version series. That means a constraint like `flepimop2~=0.0` today, and `flepimop2~=1.0` once the project reaches v1.

### Step 2: Configure `pyproject.toml`

Edit the generated `pyproject.toml` file to configure the namespace package and add `flepimop2` as a dependency. Your `pyproject.toml` should look like this:

```toml
[project]
name = "flepimop2-npz-backend"
version = "0.1.0"
description = "An external provider for flepimop2 for saving and reading npz files."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "flepimop2~=0.0",
    "numpy>=2.3.5",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/flepimop2"]
```

The critical configuration here is `[tool.hatch.build.targets.wheel]`, which tells Hatch to package everything under `src/flepimop2` as part of the `flepimop2` namespace.

### Step 3: Create the Directory Structure

Create the following directory structure for your namespace package:

```bash
rm -r src/
mkdir -p src/flepimop2/backend/npz
```

Do not create `__init__.py` files in `src/flepimop2/` or `src/flepimop2/backend/`. These directories must remain empty to function as namespace packages. Only create an `__init__.py` file in the leaf module directory.

Your directory structure should look like this:

```
flepimop2-npz-backend/
├── pyproject.toml
├── README.md
└── src/
    └── flepimop2/          # NO __init__.py (namespace package)
        └── backend/        # NO __init__.py (namespace package)
            └── npz/        # This directory WILL have __init__.py
                └── __init__.py
```

The lack of `__init__.py` files in the intermediate directories (`flepimop2/` and `backend/`) is what makes them namespace packages, allowing multiple packages to contribute to the same namespace without conflicts.

### Step 4: Implement the `NpzBackend` Class

Now we'll implement the `NpzBackend` class in `src/flepimop2/backend/npz/__init__.py`. Backends must implement the [`BackendABC`][flepimop2.abcs.BackendABC] interface. Since `BackendABC` already inherits from `ModuleBase` (a Pydantic `BaseModel`), your class automatically gains configuration parsing and validation - no separate `build` function is needed.

```python
"""NPZ backend for flepimop2."""

import os
from pathlib import Path

import numpy as np
from pydantic import Field, field_validator

from flepimop2.backend.abc import BackendABC
from flepimop2.meta import RunMeta
from flepimop2.typing import Float64NDArray


class NpzBackend(BackendABC, module="npz"):
    """NPZ backend for saving numpy arrays to .npz files."""

    root: Path = Field(default_factory=lambda: Path.cwd() / "model_output")
    compressed: bool = Field(default=True, description="Use compression when saving")

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
        filename = f"{name_part}{run_meta.action}_{timestamp_str}.npz"
        return self.root / filename

    def _save(self, data: Float64NDArray, run_meta: RunMeta) -> None:
        """
        Save a numpy array to an NPZ file.

        Args:
            data: The numpy array to save.
            run_meta: Metadata about the current run.
        """
        file_path = self._get_file_path(run_meta)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if self.compressed:
            np.savez_compressed(file_path, data=data)
        else:
            np.savez(file_path, data=data)

    def _read(self, run_meta: RunMeta) -> Float64NDArray:
        """
        Read a numpy array from an NPZ file.

        Args:
            run_meta: Metadata about the current run.

        Returns:
            The numpy array read from the NPZ file.
        """
        file_path = self._get_file_path(run_meta)
        with np.load(file_path) as npz_file:
            return npz_file["data"]
```

The `module="npz"` class argument is the required API. It resolves to the fully qualified module path `"flepimop2.backend.npz"` and also constrains the matching Pydantic field to that value. The explicit annotation form is also supported:

```python
from typing import Literal


class NpzBackend(BackendABC):
    module: Literal["flepimop2.backend.npz"] = "flepimop2.backend.npz"
    ...
```

Key points of this implementation:

- The class inherits from [`BackendABC`][flepimop2.abcs.BackendABC], which already provides the Pydantic `BaseModel` foundation via `ModuleBase`.
- The `module="npz"` class argument resolves the exact module path and constrains the corresponding Pydantic field to that value.
- Pydantic's `Field` is used to define configuration options with defaults and descriptions.
- Field validators can be used for custom validation logic.
- No separate `build` function is needed - `flepimop2` calls `NpzBackend.model_validate(config)` directly.

### Step 5: Install the Package

Install your package in development mode:

```bash
uv pip install -e .
```

This makes the `flepimop2.backend.npz` module available to `flepimop2`.

### Step 6: Use the Backend in a Configuration File

Now you can use your custom backend in a `flepimop2` configuration file with `module: 'npz'` like so:

```yaml
backend:
  - module: 'npz'
    root: './npz_output'
    compressed: true
```

When `flepimop2` processes this configuration:

1. It sees `module: 'npz'` in the backend section.
2. It prepends `flepimop2.backend.` to resolve it to `flepimop2.backend.npz`.
3. It imports the module from your external package.
4. It finds the `NpzBackend` class (the `BackendABC` subclass defined in that module).
5. It calls `NpzBackend.model_validate(config)` to construct the instance.

## Testing Your External Provider Package

It's important to test your external provider package to ensure it integrates correctly with `flepimop2`. Here's a minimal unit test:

```python
"""Unit test for NPZ backend."""

from pathlib import Path
import numpy as np
from flepimop2.backend.npz import NpzBackend
from flepimop2.meta import RunMeta


def test_npz_backend_save_and_load(tmp_path: Path) -> None:
    """Test that NPZ backend can save and load data."""
    # Create backend instance
    backend = NpzBackend(root=tmp_path, compressed=True)

    # Create test data
    test_data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])

    # Create run metadata
    run_meta = RunMeta(name="test", action="simulate")

    # Save data
    backend.save(test_data, run_meta)

    # Verify file was created
    output_files = list(tmp_path.glob("*.npz"))
    assert len(output_files) == 1

    # Load data and verify it matches
    loaded_data = backend.read(run_meta)
    np.testing.assert_array_equal(loaded_data, test_data)
```

## Licensing

Since `flepimop2` is [licensed under GPLv3](../license.md) external provider packages must also be licensed under GPLv3. However, since external provider packages are a secondary python package that both depend on `flepimop2` and depend on your core python package your core python package does not need to be licensed under GPLv3.

For more detailed questions around licensing please feel free to reach out for guidance.

## Summary

This tutorial covered:

- What external provider packages are and why they're useful.
- How PEP 420 namespace packages enable seamless integration with `flepimop2`.
- Creating a new external provider package using `uv` and `hatchling`.
- Proper directory structure for namespace packages (no `__init__.py` in intermediate directories).
- Implementing module classes by inheriting from the appropriate ABC (e.g., `BackendABC`), which provides Pydantic validation automatically.
- Using your external provider package in `flepimop2` configuration files.
- Testing your external provider package.

With this knowledge, you can extend `flepimop2` with custom systems, engines, backends, and processors that integrate seamlessly with the core framework.

<!-- skip: end -->
