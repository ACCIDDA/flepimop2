"""Weekly hospitalization incidence spaghetti plots for legacy grid panels.

3x3 layout: rows = S0 fractions (0.3, 0.5, 0.7), cols = R0 values (1.1, 2.0, 4.0).
Each panel overlays weekly new hospital admissions as % of population for every
(t_start, cap_l) scenario.

New admissions are estimated from the H prevalence trajectory as:
    inflow(t) = ΔH(t) + H(t) / t_hosp
which follows from: dH/dt = inflow - H/t_hosp.
Weekly incidence = sum of daily inflow over each 7-day window.

Lines are coloured by campaign start time (t_start); line style varies by cap_l.
Uses the latest batch from model_output/legacy_r0_s0_batches.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import yaml
from flepimop2.configuration import ConfigurationModel

if TYPE_CHECKING:
    from matplotlib.axes import Axes

ARG_LEN_MIN = 2
SWEEP_SCENARIO_NAME = "vax_campaign"
PANEL_SCENARIO_NAME = "panel_grid"
H_COL_INDICES = [7, 8, 9]
LINESTYLES = ["-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 2))]

FULL_WEEK_DAYS = 7
_PCT_THRESHOLD_LOW = 0.01
_PCT_THRESHOLD_MID = 0.1


def _pct_label(v: float, _: object) -> str:
    """Adaptive percentage formatter that switches precision based on magnitude."""
    if v == 0.0:
        return "0%"
    abs_v = abs(v)
    if abs_v < _PCT_THRESHOLD_LOW:
        return f"{v:.3f}%"
    if abs_v < _PCT_THRESHOLD_MID:
        return f"{v:.2f}%"
    return f"{v:.2f}%"


@dataclass(frozen=True)
class IncidenceMeta:
    """Grid, population, and model metadata."""

    t_start_vals: list[float]
    cap_l_vals: list[float]
    r0_values: list[float]
    s_frac_values: list[float]
    n0: float
    t_hosp: float


@dataclass(frozen=True)
class IncidencePanelMeta:
    """Per-panel rendering options."""

    r0_val: float
    s_frac: float
    show_title: bool
    show_row_label: bool
    show_xlabel: bool


def _scenario_param_values(
    cfg: dict[str, Any],
    scenario_name: str,
    param_name: str,
) -> list[float]:
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
    return f"{value:.3f}".rstrip("0").rstrip(".").replace(".", "p")


def _latest_csv_by_index(
    results_dir: Path, pattern: str = "scenario_*.csv"
) -> list[Path]:
    by_index: dict[int, Path] = {}
    for f in results_dir.glob(pattern):
        match = re.search(r"scenario_(\d+)", f.name)
        if not match:
            continue
        idx = int(match.group(1))
        if idx not in by_index or f.name > by_index[idx].name:
            by_index[idx] = f
    return [by_index[i] for i in sorted(by_index)]


def _weekly_incidence_pct(
    csv_file: Path, n0: float, t_hosp: float
) -> tuple[np.ndarray, np.ndarray]:
    """Return (week_midpoints, weekly_incidence_pct) arrays.

    Incidence = inflow into H = ΔH + H/t_hosp (daily), summed per 7-day windows.
    Only full 7-day bins are retained to avoid endpoint drop artifacts.
    Returned as % of population.
    """
    df = pd.read_csv(csv_file, header=None)
    time = df.iloc[:, 0].to_numpy()
    h_total = df.iloc[:, H_COL_INDICES].sum(axis=1).to_numpy()

    # Daily inflow: dH/dt + H/t_hosp  (discrete: ΔH + H[t]/t_hosp)
    delta_h = np.diff(h_total)
    daily_inflow = delta_h + h_total[:-1] / t_hosp  # shape (T-1,)
    t_mid = 0.5 * (time[:-1] + time[1:])

    # Group into 7-day windows using midpoints.
    # Drop any incomplete final week (count < 7) to avoid artificial endpoint dips.
    week_starts = np.floor(t_mid / 7.0) * 7.0
    unique_starts, counts = np.unique(week_starts, return_counts=True)
    full_week_starts = unique_starts[counts == FULL_WEEK_DAYS]
    week_mids = full_week_starts + 3.5

    weekly = np.array(
        [daily_inflow[week_starts == ws].sum() for ws in full_week_starts]
    )
    # Clip to non-negative (numerical noise can produce tiny negatives)
    weekly = np.maximum(weekly, 0.0)

    return week_mids, weekly / n0 * 100.0


def _draw_incidence_panel(
    ax: Axes,
    panel_dir: Path,
    meta: IncidenceMeta,
    panel: IncidencePanelMeta,
) -> None:
    """Overlay weekly incidence trajectories for one (r0, s_frac) panel."""
    csv_files = _latest_csv_by_index(panel_dir)
    expected = len(meta.t_start_vals) * len(meta.cap_l_vals)
    if len(csv_files) != expected:
        msg = f"Expected {expected} CSVs in {panel_dir}, found {len(csv_files)}"
        raise ValueError(msg)

    t_cmap = plt.cm.plasma_r
    t_norm = plt.Normalize(vmin=min(meta.t_start_vals), vmax=max(meta.t_start_vals))

    for scenario_idx, csv_file in enumerate(csv_files):
        t_start_idx = scenario_idx // len(meta.cap_l_vals)
        cap_l_idx = scenario_idx % len(meta.cap_l_vals)

        week_mids, weekly_pct = _weekly_incidence_pct(csv_file, meta.n0, meta.t_hosp)

        t_start = meta.t_start_vals[t_start_idx]
        ls = LINESTYLES[cap_l_idx % len(LINESTYLES)]
        color = t_cmap(t_norm(t_start))

        ax.plot(
            week_mids,
            weekly_pct,
            color=color,
            linestyle=ls,
            linewidth=0.8,
            alpha=0.75,
        )

    ax.xaxis.set_major_locator(mticker.MultipleLocator(100))
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(50))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_pct_label))
    ax.tick_params(axis="both", labelsize=7)
    ax.grid(visible=True, linewidth=0.3, alpha=0.4)

    if panel.show_title:
        ax.set_title(f"R0={panel.r0_val:.1f}", fontsize=12, fontweight="bold")

    if panel.show_row_label:
        ax.set_ylabel(
            (
                f"S0={round(panel.s_frac * 100)}%\n"
                "Weekly Hospital Admissions\n(% population, 7-day total)"
            ),
            fontsize=9,
            fontweight="bold",
        )

    if panel.show_xlabel:
        ax.set_xlabel("Time (days)", fontsize=9)


def _make_incidence_figure(
    batch_root: Path,
    meta: IncidenceMeta,
    output_path: Path,
) -> None:
    """Render the 3x3 weekly incidence spaghetti figure."""
    n_rows = len(meta.s_frac_values)
    n_cols = len(meta.r0_values)

    fig, axes = plt.subplots(
        nrows=n_rows,
        ncols=n_cols,
        figsize=(16, 12),
        sharex=True,
    )

    if n_rows == 1 and n_cols == 1:
        axes_2d = np.array([[axes]])
    elif n_rows == 1:
        axes_2d = np.array([axes])
    elif n_cols == 1:
        axes_2d = np.array([[ax] for ax in axes])
    else:
        axes_2d = axes

    for row, s_frac in enumerate(meta.s_frac_values):
        for col, r0_val in enumerate(meta.r0_values):
            panel_dir = batch_root / (
                f"r0_{_slug_float(r0_val)}__sfrac_{_slug_float(s_frac)}"
            )
            panel = IncidencePanelMeta(
                r0_val=r0_val,
                s_frac=s_frac,
                show_title=row == 0,
                show_row_label=col == 0,
                show_xlabel=row == n_rows - 1,
            )
            _draw_incidence_panel(axes_2d[row, col], panel_dir, meta, panel)

    # Colourbar for t_start (dedicated external axis, avoids covering panel data)
    t_cmap = plt.cm.plasma_r
    t_norm = plt.Normalize(vmin=min(meta.t_start_vals), vmax=max(meta.t_start_vals))
    sm = plt.cm.ScalarMappable(cmap=t_cmap, norm=t_norm)
    sm.set_array([])
    cax = fig.add_axes([0.90, 0.20, 0.02, 0.60])
    cbar = fig.colorbar(sm, cax=cax)
    cbar.set_label("Campaign Start Day", fontsize=11, fontweight="bold")

    # Legend for cap_l (linestyles)
    handles = [
        plt.Line2D(
            [0],
            [0],
            color="grey",
            linestyle=LINESTYLES[i % len(LINESTYLES)],
            linewidth=1.2,
            label=f"cap_l={v:.2f}",
        )
        for i, v in enumerate(meta.cap_l_vals)
    ]
    fig.legend(
        handles=handles,
        title="Coverage Cap",
        fontsize=7,
        title_fontsize=8,
        loc="lower center",
        ncol=len(meta.cap_l_vals),
        bbox_to_anchor=(0.45, -0.01),
        framealpha=0.9,
    )

    fig.suptitle(
        "Weekly Hospital Admissions by R0 and Initial Susceptible Share\n"
        "colour = campaign start day, line style = coverage cap",
        fontsize=13,
        fontweight="bold",
    )
    fig.subplots_adjust(
        left=0.10,
        right=0.87,
        bottom=0.10,
        top=0.88,
        wspace=0.14,
        hspace=0.10,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    """Load latest batch and render weekly hospitalization incidence spaghetti."""
    args = sys.argv[1:]
    if len(args) < ARG_LEN_MIN:
        msg = (
            "python postprocessing/scenario_spaghetti_incidence_legacy.py "
            "<config.yml> <output.png>"
        )
        raise SystemExit(msg)

    cfg_path = Path(args[0])
    output_path = Path(args[1])

    with cfg_path.open() as f:
        raw_cfg = yaml.safe_load(f)

    config_model = ConfigurationModel.from_yaml(cfg_path)
    t_start_vals = _scenario_param_values(raw_cfg, SWEEP_SCENARIO_NAME, "t_start")
    cap_l_vals = _scenario_param_values(raw_cfg, SWEEP_SCENARIO_NAME, "cap_l")
    r0_values = _scenario_param_values(raw_cfg, PANEL_SCENARIO_NAME, "r0")
    s_frac_values = _scenario_param_values(raw_cfg, PANEL_SCENARIO_NAME, "s_frac")
    n0 = float(config_model.parameters["n0"].value)
    t_hosp = float(config_model.parameters["t_hosp"].value)

    meta = IncidenceMeta(
        t_start_vals=t_start_vals,
        cap_l_vals=cap_l_vals,
        r0_values=r0_values,
        s_frac_values=s_frac_values,
        n0=n0,
        t_hosp=t_hosp,
    )

    base_root = Path("model_output") / "legacy_r0_s0_batches"
    latest_txt = base_root / "LATEST"
    if not latest_txt.exists():
        msg = (
            "No batch marker found. Run scenario_heatmap_3x3_run_batch_and_plot first."
        )
        raise FileNotFoundError(msg)
    batch_root = base_root / latest_txt.read_text().strip()

    _make_incidence_figure(batch_root, meta, output_path)
    sys.stdout.write(f"Saved weekly incidence spaghetti to {output_path}\n")


if __name__ == "__main__":
    main()
