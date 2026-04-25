# postprocessing/SIR_plot_op_engine.py
"""OP Engine SIR plot generator using flepimop2's public configuration API."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from flepimop2.configuration import ConfigurationModel

ARG_LEN = 2


def _latest_csv(results_dir: Path) -> Path:
    csvs = sorted(results_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime)
    if not csvs:
        msg = f"No CSV files found in results directory: {results_dir}"
        raise FileNotFoundError(msg)
    return csvs[-1]


def _resolve_results_dir(config_model: ConfigurationModel) -> Path:
    """Resolve the CSV backend output directory using flepimop2's ConfigurationModel.

    This mirrors the CLI's default behavior:
    - Use the first simulate target by insertion order.
    - Use that target's backend name (defaulting to "default" if absent).
    - Read the backend config and use its root (defaulting to "model_output").

    Args:
        config_model: The validated configuration model.

    Raises:
        ValueError: If the simulate block is empty.
        KeyError: If the backend name is not found in the backends block.

    Returns:
        Path to the results directory.
    """
    simulate_block = config_model.simulate
    if not simulate_block:
        msg = "config.simulate must be non-empty"
        raise ValueError(msg)

    # CLI default behavior: first simulate target by insertion order.
    first_sim = next(iter(simulate_block.values()))

    backend_name = getattr(first_sim, "backend", None) or "default"

    # NOTE: Backends are stored as ModuleModel instances in the config model, and may
    # not expose backend-specific fields (e.g., CsvBackend.root) directly. We therefore
    # resolve the root path from the serialized config with a sensible default.
    # See issue: Backend outputs cannot be discovered programmatically without RunMeta.
    backend_model = config_model.backends.get(backend_name)
    if backend_model is None:
        msg = f"simulate backend {backend_name!r} not found in config.backends"
        raise KeyError(msg)

    backend_cfg = backend_model.model_dump()

    # Prefer an explicit root if present; otherwise fall back to the default.
    # Some schema variants may nest backend-specific options.
    root = (
        backend_cfg.get("root")
        or backend_cfg.get("config", {}).get("root")
        or backend_cfg.get("params", {}).get("root")
        or backend_cfg.get("settings", {}).get("root")
        or "model_output"
    )

    return Path(root)

def _resolve_state_names(config_model: ConfigurationModel) -> list[str]:
    """Resolve compartment state names from the first system in the configuration.

    Args:
        config_model: The validated configuration model

    Raises:
        ValueError: If no systems are defined or the spec does not declare a state list.

    Returns:
        List of state variable names in spec order.
    """
    if not config_model.systems:
        msg = "config.system must define at least one system"
        raise ValueError(msg)

    first_system = next(iter(config_model.systems.values()))
    state_names = first_system.model_dump().get("spec", {}).get("state", [])

    if not state_names:
        msg = "system spec must define a non-empty 'state' list"
        raise ValueError(msg)
    return list(state_names)


def main() -> None:
    """Generate SIR plot from op_engine simulation results.

    Raises:
        SystemExit: If len(args) != ARG_LEN
        ValueError: If df.shape[1] is less than the minimum 4 columns required
    """
    args = sys.argv[1:]
    if len(args) != ARG_LEN:
        msg = "python postprocessing/SIR_plot_op_engine.py <config.yml> <output.png>"
        raise SystemExit(msg)

    cfg_path = Path(args[0])
    out_path = Path(args[1])

    # Use flepimop2's config API (validated/typed) instead of manual YAML parsing.
    config_model = ConfigurationModel.from_yaml(cfg_path)

    state_names = _resolve_state_names(config_model)
    n_expected_cols = 1 + len(state_names) # time-column plus one per compartment

    results_path = _resolve_results_dir(config_model)
    latest = _latest_csv(results_path)

    df = pd.read_csv(latest, header=None)

    # Expect (T, 1 + n_state) => time + SIR columns
    if df.shape[1] < n_expected_cols:
        msg = (
            f"Expected at least {n_expected_cols} columns "
            f"(time + {state_names}); got {df.shape[1]}"
        )
        raise ValueError(msg)

    df = df.iloc[:, :n_expected_cols]
    df.columns = ["time"] + state_names

    plt.figure(figsize=(6, 4))
    for state in state_names:
        plt.plot(df["time"], df[state], label=state)
    plt.grid(visible=True)
    plt.legend()
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.title("Compartmental Model Plot (op_engine via flepimop2)")
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()


if __name__ == "__main__":
    main()
