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
"""Integration test for the documentation quick start flow."""

from pathlib import Path

from flepimop2.testing import flepimop2_run, project_skeleton


def test_quick_start_simulate(repo_root: Path, tmp_path: Path) -> None:
    """
    Create a skeleton project, add plugins + config from docs, then simulate.

    This verifies the documentation quick start path remains functional.
    """
    project_skeleton(
        tmp_path,
        copy_files={
            repo_root / "docs/assets/scenarios_config.yaml": Path(
                "configs/scenarios_config.yaml"
            ),
            repo_root / "docs/assets/SIR.py": Path("model_input/plugins/SIR.py"),
            repo_root / "docs/assets/solve_ivp.py": Path(
                "model_input/plugins/solve_ivp.py"
            ),
        },
        dependencies=["scipy"],
    )

    result = flepimop2_run(
        "simulate",
        args=["configs/scenarios_config.yaml"],
        cwd=tmp_path,
    )
    assert result.returncode == 0
    output_files = list((tmp_path / "model_output").glob("*.csv"))
    assert len(output_files) == 9
