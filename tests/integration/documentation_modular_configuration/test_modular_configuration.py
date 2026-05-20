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
"""Integration test for the modular-configuration guide."""

import subprocess  # noqa: S404
from pathlib import Path

import pytest
from yaml import safe_load

from flepimop2.testing import flepimop2_run, project_skeleton
from flepimop2.typing import ExitCode


def test_modular_configuration_guide(repo_root: Path, tmp_path: Path) -> None:
    """
    Build modular configs with `patch`, then run a simulation from the result.

    This verifies the documentation guide's modular patch workflow remains usable.
    """
    asset_root = repo_root / "docs/assets/modular-configuration"

    project_skeleton(
        tmp_path,
        copy_files={
            asset_root / "configs/model.yaml": Path("configs/model.yaml"),
            asset_root / "configs/parameters/initial-state.yaml": Path(
                "configs/parameters/initial-state.yaml",
            ),
            asset_root / "configs/parameters/transmission-baseline.yaml": Path(
                "configs/parameters/transmission-baseline.yaml",
            ),
            asset_root / "configs/parameters/transmission-high.yaml": Path(
                "configs/parameters/transmission-high.yaml",
            ),
            asset_root / "configs/parameters/recovery-standard.yaml": Path(
                "configs/parameters/recovery-standard.yaml",
            ),
            asset_root / "model_input/plugins/SIR.py": Path(
                "model_input/plugins/SIR.py",
            ),
            asset_root / "model_input/plugins/solve_ivp.py": Path(
                "model_input/plugins/solve_ivp.py",
            ),
        },
        dependencies=["scipy"],
    )

    assert (tmp_path / "configs" / "built" / ".gitignore").is_file()

    stdout_result = flepimop2_run(
        "patch",
        args=[
            "configs/model.yaml",
            "configs/parameters/initial-state.yaml",
            "configs/parameters/transmission-baseline.yaml",
            "configs/parameters/recovery-standard.yaml",
        ],
        cwd=tmp_path,
    )

    assert stdout_result.returncode == 0
    stdout_config = safe_load(stdout_result.stdout)
    assert stdout_config["parameters"] == {
        "s0": 999.0,
        "i0": 1.0,
        "r0": 0.0,
        "beta": 0.3,
        "gamma": 0.1,
    }
    assert stdout_config["simulate"]["demo"]["backend"] == "default"

    error_result = subprocess.run(  # noqa: S603
        [
            str(tmp_path / ".venv" / "bin" / "flepimop2"),
            "patch",
            "configs/model.yaml",
            "configs/parameters/initial-state.yaml",
            "configs/parameters/transmission-baseline.yaml",
            "configs/parameters/transmission-high.yaml",
            "configs/parameters/recovery-standard.yaml",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )

    assert error_result.returncode == ExitCode.CONFIGURATION
    assert "Cannot patch configuration under conflict='error'" in error_result.stdout
    assert "parameters=['beta']" in error_result.stdout

    built_config = tmp_path / "configs" / "built" / "high-transmission.yaml"
    output_result = flepimop2_run(
        "patch",
        args=[
            "--patch-mode",
            "replace",
            "--output",
            "configs/built/high-transmission.yaml",
            "configs/model.yaml",
            "configs/parameters/initial-state.yaml",
            "configs/parameters/transmission-baseline.yaml",
            "configs/parameters/transmission-high.yaml",
            "configs/parameters/recovery-standard.yaml",
        ],
        cwd=tmp_path,
    )

    assert output_result.returncode == 0
    assert not output_result.stdout
    built_payload = safe_load(built_config.read_text(encoding="utf-8"))
    assert built_payload["parameters"]["beta"] == pytest.approx(0.45)

    simulate_result = flepimop2_run(
        "simulate",
        args=["configs/built/high-transmission.yaml"],
        cwd=tmp_path,
    )

    assert simulate_result.returncode == 0
    assert list((tmp_path / "model_output").glob("*.csv"))
