"""Integration test for external provider functionality."""

import re
import subprocess  # noqa: S404
from pathlib import Path

import pytest

from flepimop2._testing import external_provider_project, which_uv


def test_external_provider(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """
    Test external provider functionality.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory provided by pytest.

    Notes:
        This test runs the simulation using the external provider package and checks
        that the output file is created as expected. It verifies that before running
        the simulation, there are no output files, and after running, exactly one
        output file is created with the expected naming pattern.
    """
    # Setup
    uv = which_uv()
    cwd = Path(__file__).parent.resolve()
    external_provider_project(
        tmp_path,
        uv=uv,
        src_dest_map={
            cwd / "config.yaml": Path("config.yaml"),
            cwd / "runner.py": Path("external_provider")
            / "src"
            / "external_provider"
            / "runner.py",
            cwd / "stepper.py": Path("external_provider")
            / "src"
            / "external_provider"
            / "stepper.py",
        },
    )
    monkeypatch.chdir(tmp_path)
    # Pre-test
    assert len(list((tmp_path / "model_output").iterdir())) == 0
    # Run the simulation using the external provider package
    result = subprocess.run(  # noqa: S603
        [
            str(tmp_path / ".venv" / "bin" / "flepimop2"),
            "simulate",
            "config.yaml",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=True,
    )
    # Post-test
    assert result.returncode == 0
    model_output = list((tmp_path / "model_output").iterdir())
    assert len(model_output) == 1
    csv = model_output[0]
    assert re.match(r"^simulate_\d{8}_\d{6}\.csv$", csv.name)
    assert csv.stat().st_size > 0
