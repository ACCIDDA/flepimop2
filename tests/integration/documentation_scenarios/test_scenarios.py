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
            repo_root / "docs/assets/scenarios_config.yaml": Path("configs/scenarios_config.yaml"),
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
    # confirm the simulation ran successfully by checking for 9 output files (1 for each scenario)
    output_files = list((tmp_path / "model_output").glob("*.csv"))
    assert len(output_files) == 9

