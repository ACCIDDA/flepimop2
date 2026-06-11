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
"""Integration test for the batch-jobs guide."""

from pathlib import Path

from flepimop2.testing import flepimop2_run, project_skeleton


def test_batch_jobs_guide(repo_root: Path, tmp_path: Path) -> None:
    """
    Run `flepimop2 job simulate` with the shell backend from the batch-jobs guide.

    This verifies that the guide's config and CLI invocation remain functional.
    """
    asset_root = repo_root / "docs/assets/batch-jobs-guide"

    project_skeleton(
        tmp_path,
        copy_files={
            asset_root / "configs/config.yaml": Path("configs/config.yaml"),
            asset_root / "model_input/plugins/SIR.py": Path(
                "model_input/plugins/SIR.py"
            ),
            asset_root / "model_input/plugins/solve_ivp.py": Path(
                "model_input/plugins/solve_ivp.py"
            ),
        },
        dependencies=["scipy"],
    )

    result = flepimop2_run(
        "job",
        args=["simulate", "configs/config.yaml"],
        cwd=tmp_path,
    )
    assert result.returncode == 0

    output_files = list((tmp_path / "model_output").glob("*.csv"))
    assert len(output_files) == 1

    # Submitting through the shell backend caches a handle and a summary.
    cache_dir = tmp_path / ".flepimop2_cache" / "job"
    handle_files = list((cache_dir / "handles").glob("*.json"))
    assert len(handle_files) == 1
    assert (cache_dir / "summary.json").is_file()

    # `job list` reports the cached shell job with a resolved status.
    list_result = flepimop2_run("job", args=["list"], cwd=tmp_path)
    assert list_result.returncode == 0
    assert "shell-" in list_result.stdout

    # The config uses `detach: false`, so the blocking job's return code yields
    # a definite, successful status.
    assert "status=successful" in list_result.stdout

    # `job status` reconstructs the backend from the cached config and reports
    # the same job. The handle file is named `<backend>-<job_id>.json`.
    job_key = handle_files[0].stem
    status_result = flepimop2_run("job", args=["status", job_key], cwd=tmp_path)
    assert status_result.returncode == 0
    assert "status=successful" in status_result.stdout
