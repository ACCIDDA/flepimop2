"""Integration test for external provider functionality."""

import re
from pathlib import Path

import pytest

from flepimop2.testing import external_provider_package, flepimop2_run


def test_external_provider(
    monkeypatch: pytest.MonkeyPatch, repo_root: Path, tmp_path: Path
) -> None:
    """
    Test external provider functionality.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        repo_root: Path to the repository root.
        tmp_path: Temporary directory provided by pytest.

    Notes:
        This test runs the simulation using the external provider package and checks
        that the output file is created as expected. It verifies that before running
        the simulation, there are no output files, and after running, exactly one
        output file is created with the expected naming pattern.

    """
    # Setup
    external_provider_package(
        tmp_path,
        copy_files={
            repo_root / "tests/integration/external_provider/config.yaml": Path(
                "config.yaml"
            ),
            repo_root / "tests/integration/external_provider/euler.py": Path(
                "external_provider/src/flepimop2/engine/euler.py"
            ),
            repo_root / "tests/integration/external_provider/sir.py": Path(
                "external_provider/src/flepimop2/system/sir.py"
            ),
        },
    )
    monkeypatch.chdir(tmp_path)
    # Pre-test
    assert len(list((tmp_path / "model_output").iterdir())) == 0
    # Run the simulation using the external provider package
    result = flepimop2_run(
        "simulate",
        args=["config.yaml"],
        cwd=tmp_path,
    )
    # Post-test
    assert result.returncode == 0
    model_output = list((tmp_path / "model_output").iterdir())
    assert len(model_output) == 1
    csv = model_output[0]
    assert re.match(r"^simulate_\d{8}_\d{6}\.csv$", csv.name)
    assert csv.stat().st_size > 0
