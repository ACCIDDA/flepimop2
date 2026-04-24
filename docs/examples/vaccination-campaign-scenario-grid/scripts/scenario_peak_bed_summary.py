"""Simplified summary plot for peak hospital occupancy (legacy grid).

Produces a faceted scatter summary by S0 level:
- x-axis: R0
- y-axis: peak occupancy as % of available beds
- color: campaign start day (t_start)
- marker shape: coverage cap (cap_l)

A black median line is overlaid for each S0 facet to show the dominant R0 trend.
Uses the latest batch from model_output/legacy_r0_s0_batches.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
import yaml

try:
    import matplotlib.pyplot as plt  # type: ignore[import-not-found]
    import pandas as pd  # type: ignore[import-untyped]
except ModuleNotFoundError:
    plt = cast("Any", None)
    pd = cast("Any", None)

from flepimop2.configuration import ConfigurationModel

ARG_LEN_MIN = 2
SWEEP_SCENARIO_NAME = "vax_campaign"
PANEL_SCENARIO_NAME = "panel_grid"
H_COL_INDICES = [7, 8, 9]
BEDS_PER_1000 = 2.3
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "<", ">"]


@dataclass(frozen=True)
class PlotMeta:
    """Metadata needed for rendering the peak occupancy summary."""

    t_start_vals: list[float]
    cap_l_vals: list[float]
    r0_values: list[float]
    s_frac_values: list[float]
    available_beds: float


def _scenario_param_values(
    cfg: dict[str, Any],
    scenario_name: str,
    param_name: str,
) -> list[float]:
    """Read scenario parameter values from raw YAML config."""
    scenarios = cfg.get("scenarios")
    if not isinstance(scenarios, dict):
        msg = "No scenarios mapping found in config"
        raise TypeError(msg)
    scenario = scenarios.get(scenario_name)
    if not isinstance(scenario, dict):
        msg = f"Scenario {scenario_name!r} not found"
        raise KeyError(msg)
    params = scenario.get("parameters")
    if not isinstance(params, dict):
        msg = f"Scenario {scenario_name!r} has no parameters mapping"
        raise TypeError(msg)
    if param_name not in params:
        msg = f"Parameter {param_name!r} not found in scenarios[{scenario_name!r}]"
        raise KeyError(msg)
    return [float(v) for v in params[param_name]]


def _slug_float(value: float) -> str:
    """Convert a float to a filesystem-safe token."""
    return f"{value:.3f}".rstrip("0").rstrip(".").replace(".", "p")


def _latest_csv_by_index(
    results_dir: Path, pattern: str = "scenario_*.csv"
) -> list[Path]:
    """Get one CSV per scenario index (latest file by name), sorted numerically."""
    by_index: dict[int, Path] = {}
    for f in results_dir.glob(pattern):
        match = re.search(r"scenario_(\d+)", f.name)
        if not match:
            continue
        idx = int(match.group(1))
        if idx not in by_index or f.name > by_index[idx].name:
            by_index[idx] = f
    return [by_index[i] for i in sorted(by_index)]


def _build_peak_dataframe(batch_root: Path, meta: PlotMeta) -> pd.DataFrame:
    """Build one row per scenario with peak occupancy (% beds)."""
    rows: list[dict[str, float]] = []

    for s_frac in meta.s_frac_values:
        for r0_val in meta.r0_values:
            panel_dir = batch_root / (
                f"r0_{_slug_float(r0_val)}__sfrac_{_slug_float(s_frac)}"
            )
            csv_files = _latest_csv_by_index(panel_dir)
            expected = len(meta.t_start_vals) * len(meta.cap_l_vals)
            if len(csv_files) != expected:
                msg = f"Expected {expected} CSVs in {panel_dir}, found {len(csv_files)}"
                raise ValueError(msg)

            for scenario_idx, csv_file in enumerate(csv_files):
                t_start_idx = scenario_idx // len(meta.cap_l_vals)
                cap_l_idx = scenario_idx % len(meta.cap_l_vals)

                df = pd.read_csv(csv_file, header=None)
                h_totals = df.iloc[:, H_COL_INDICES].sum(axis=1).to_numpy()
                peak_h = float(h_totals.max())
                peak_bed_pct = 100.0 * peak_h / meta.available_beds

                rows.append({
                    "s_frac": s_frac,
                    "r0": r0_val,
                    "t_start": meta.t_start_vals[t_start_idx],
                    "cap_l": meta.cap_l_vals[cap_l_idx],
                    "peak_bed_pct": peak_bed_pct,
                })

    return pd.DataFrame(rows)


def _make_summary_figure(  # noqa: PLR0914
    df: pd.DataFrame, meta: PlotMeta, output_path: Path
) -> None:
    """Render faceted scatter summary with median trend by R0."""
    n_cols = len(meta.s_frac_values)
    fig, axes = plt.subplots(1, n_cols, figsize=(17, 5.8), sharey=True)
    axes_arr = [axes] if n_cols == 1 else list(axes)

    t_norm = plt.Normalize(vmin=min(meta.t_start_vals), vmax=max(meta.t_start_vals))
    cmap = plt.cm.plasma_r

    cap_offsets = np.linspace(-0.16, 0.16, len(meta.cap_l_vals))
    marker_map = {
        cap: MARKERS[i % len(MARKERS)] for i, cap in enumerate(meta.cap_l_vals)
    }

    for col, s_frac in enumerate(meta.s_frac_values):
        ax = axes_arr[col]
        sdf = df[df["s_frac"] == s_frac]

        for cap_idx, cap_l in enumerate(meta.cap_l_vals):
            cdf = sdf[sdf["cap_l"] == cap_l]
            x_vals = cdf["r0"].to_numpy() + cap_offsets[cap_idx]
            sc = ax.scatter(
                x_vals,
                cdf["peak_bed_pct"].to_numpy(),
                c=cdf["t_start"].to_numpy(),
                cmap=cmap,
                norm=t_norm,
                marker=marker_map[cap_l],
                s=26,
                alpha=0.70,
                linewidths=0.15,
                edgecolors="black",
            )

        med = sdf.groupby("r0", as_index=False)["peak_bed_pct"].median()
        ax.plot(
            med["r0"].to_numpy(),
            med["peak_bed_pct"].to_numpy(),
            color="black",
            linewidth=2.0,
            marker="o",
            markersize=4,
            label="Median across policy",
            zorder=5,
        )

        ax.set_title(f"S0={round(s_frac * 100)}%", fontsize=12, fontweight="bold")
        ax.set_xticks(meta.r0_values)
        ax.set_xlabel("R0")
        ax.grid(visible=True, linewidth=0.4, alpha=0.4)

        if col == 0:
            ax.set_ylabel("Peak Hospital Occupancy (% of Available Beds)")

    fig.suptitle(
        "Peak Hospital Occupancy Summary: R0 Dominates Across Policy Settings",
        fontsize=14,
        fontweight="bold",
    )

    # Marker legend for coverage cap
    marker_handles = [
        plt.Line2D(
            [0],
            [0],
            marker=marker_map[cap_l],
            color="black",
            linestyle="",
            markersize=6,
            label=f"cap_l={cap_l:.2f}",
        )
        for cap_l in meta.cap_l_vals
    ]
    axes_arr[-1].legend(
        handles=marker_handles,
        title="Coverage Cap",
        fontsize=7,
        title_fontsize=8,
        loc="upper left",
    )

    cax = fig.add_axes([0.90, 0.20, 0.02, 0.60])
    cbar = fig.colorbar(sc, cax=cax)
    cbar.set_label("Campaign Start Day", fontsize=11, fontweight="bold")

    fig.subplots_adjust(left=0.08, right=0.88, bottom=0.14, top=0.84, wspace=0.10)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:  # noqa: PLR0914
    """Load latest batch and render simplified peak occupancy summary."""
    args = sys.argv[1:]
    if len(args) < ARG_LEN_MIN:
        msg = (
            "python postprocessing/scenario_peak_bed_summary_legacy.py "
            "<config.yml> <output.png>"
        )
        raise SystemExit(msg)

    cfg_path = Path(args[0])
    output_path = Path(args[1])

    with cfg_path.open(encoding="utf-8") as f:
        raw_cfg = yaml.safe_load(f)

    config_model = ConfigurationModel.from_yaml(cfg_path)
    t_start_vals = _scenario_param_values(raw_cfg, SWEEP_SCENARIO_NAME, "t_start")
    cap_l_vals = _scenario_param_values(raw_cfg, SWEEP_SCENARIO_NAME, "cap_l")
    r0_values = _scenario_param_values(raw_cfg, PANEL_SCENARIO_NAME, "r0")
    s_frac_values = _scenario_param_values(raw_cfg, PANEL_SCENARIO_NAME, "s_frac")

    n0 = float(cast("Any", config_model.parameters["n0"]).value)
    available_beds = (BEDS_PER_1000 / 1000.0) * n0

    meta = PlotMeta(
        t_start_vals=t_start_vals,
        cap_l_vals=cap_l_vals,
        r0_values=r0_values,
        s_frac_values=s_frac_values,
        available_beds=available_beds,
    )

    base_root = Path("model_output") / "legacy_r0_s0_batches"
    latest_txt = base_root / "LATEST"
    if not latest_txt.exists():
        msg = (
            "No batch marker found. Run scenario_heatmap_3x3_run_batch_and_plot first."
        )
        raise FileNotFoundError(msg)
    batch_root = base_root / latest_txt.read_text(encoding="utf-8").strip()

    df = _build_peak_dataframe(batch_root, meta)
    _make_summary_figure(df, meta, output_path)
    sys.stdout.write(f"Saved peak occupancy summary to {output_path}\n")


if __name__ == "__main__":
    main()
