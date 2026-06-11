"""Run coarse R0/S0 sweeps and generate legacy 3x3 panel plots.

Rows: susceptible share at t=0 (S0 fraction): 30%, 50%, 70%
Cols: basic reproduction number R0: 1.1, 2.0, 4.0

Each panel is a t_start x cap_l heatmap with these outputs:
1. Hospitalization burden (% change from panel baseline policy)
2. Peak hospitalization day relative to campaign start (days)
3. Peak hospital occupancy as % of available beds
"""

from __future__ import annotations

import copy
import dataclasses
import logging
import math
import re
import shutil
import subprocess  # noqa: S404
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

import numpy as np
import yaml

try:
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt
    import pandas as pd
    from matplotlib import cm, colors
except ModuleNotFoundError:
    mpatches = cast("Any", None)
    plt = cast("Any", None)
    pd = cast("Any", None)
    cm = cast("Any", None)
    colors = cast("Any", None)

from flepimop2.configuration import ConfigurationModel

if TYPE_CHECKING:
    from matplotlib.axes import Axes

ARG_LEN_MIN = 2
EXPECTED_POSITIONAL_BURDEN_ONLY = 2
EXPECTED_POSITIONAL_ALL_METRICS = 4
SWEEP_SCENARIO_NAME = "vax_campaign"
PANEL_SCENARIO_NAME = "panel_grid"
BEDS_PER_1000 = 2.3
LOGGER = logging.getLogger(__name__)

MetricName = Literal["burden", "peak_day", "peak_bed_pct"]

_BED_PCT_INTEGER_THRESHOLD = 100.0


@dataclass(frozen=True)
class PanelMetrics:
    """Metric matrices for one (r0, s_frac) panel."""

    burden_pct_change: np.ndarray
    peak_day_relative: np.ndarray
    peak_bed_pct: np.ndarray


@dataclass(frozen=True)
class PlotMeta:
    """Metadata used to render panel figures."""

    t_start_vals: list[float]
    cap_l_vals: list[float]
    r0_values: list[float]
    s_frac_values: list[float]
    default_t_start: float
    default_cap_l: float


@dataclass(frozen=True)
class PanelDrawMeta:
    """Metadata needed to draw one subplot panel."""

    r0_val: float
    s_frac: float
    show_title: bool
    show_row_label: bool
    show_xlabel: bool
    t_start_vals: list[float]
    cap_l_vals: list[float]
    default_x: int | None
    default_y: int | None


@dataclass(frozen=True)
class FigureSpec:
    """Rendering rules for each output figure."""

    metric: MetricName
    title: str
    cbar_label: str
    cmap: str
    symmetric_about_zero: bool
    output_path: Path
    vmin: float = 0.0
    vmax: float = 1.0


@dataclass(frozen=True)
class PanelMetricMeta:
    """Inputs used to compute panel metric matrices."""

    t_start_vals: list[float]
    cap_l_vals: list[float]
    default_t_start: float
    default_cap_l: float
    available_beds: float


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


def _find_value_index(
    values: list[float], target: float, tol: float = 1e-9
) -> int | None:
    """Return the index of `target` within tolerance, else `None`."""
    for i, value in enumerate(values):
        if abs(float(value) - target) <= tol:
            return i
    return None


def _slug_float(value: float) -> str:
    """Convert a float to a filesystem-safe token."""
    return f"{value:.3f}".rstrip("0").rstrip(".").replace(".", "p")


def _set_param(cfg: dict[str, Any], name: str, value: float) -> None:
    """Set a scalar parameter value in raw YAML config."""
    params = cfg.setdefault("parameter", {})
    if name not in params:
        msg = f"Missing parameter '{name}' in config"
        raise KeyError(msg)
    params[name]["value"] = float(value)


def _set_backend_root(cfg: dict[str, Any], root: str) -> None:
    """Set backend output root in raw YAML config."""
    backend = cfg.get("backend", [])
    if not backend:
        msg = "Config has no backend section"
        raise ValueError(msg)
    if not isinstance(backend, list):
        msg = "backend section must be a list"
        raise TypeError(msg)
    backend[0]["root"] = root


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
        msg = f"Scenario {scenario_name!r} not found in config.scenarios"
        raise KeyError(msg)
    params = scenario.get("parameters")
    if not isinstance(params, dict):
        msg = f"Scenario {scenario_name!r} has no parameters mapping"
        raise TypeError(msg)
    if param_name not in params:
        msg = f"Parameter {param_name!r} not found in scenarios[{scenario_name!r}]"
        raise KeyError(msg)
    return [float(v) for v in params[param_name]]


def _extract_panel_metrics(  # noqa: PLR0914
    results_dir: Path,
    metric_meta: PanelMetricMeta,
) -> PanelMetrics:
    """Build panel matrices for all metrics."""
    csv_files = _latest_csv_by_index(results_dir)
    expected = len(metric_meta.t_start_vals) * len(metric_meta.cap_l_vals)
    if len(csv_files) != expected:
        msg = (
            f"Expected {expected} scenario files in {results_dir}, "
            f"found {len(csv_files)}. "
            "Check that scenario_sweep completed for this panel."
        )
        raise ValueError(msg)

    h_col_indices = [7, 8, 9]
    burden = np.zeros((len(metric_meta.cap_l_vals), len(metric_meta.t_start_vals)))
    peak_day_relative = np.zeros((
        len(metric_meta.cap_l_vals),
        len(metric_meta.t_start_vals),
    ))
    peak_bed_pct = np.zeros((
        len(metric_meta.cap_l_vals),
        len(metric_meta.t_start_vals),
    ))

    for scenario_idx, csv_file in enumerate(csv_files):
        df = pd.read_csv(csv_file, header=None)
        time = df.iloc[:, 0].to_numpy()
        h_totals = df.iloc[:, h_col_indices].sum(axis=1).to_numpy()

        t_start_idx = scenario_idx // len(metric_meta.cap_l_vals)
        cap_l_idx = scenario_idx % len(metric_meta.cap_l_vals)

        burden[cap_l_idx, t_start_idx] = float(np.trapezoid(h_totals, time))

        peak_idx = int(np.argmax(h_totals))
        peak_time = float(time[peak_idx])
        peak_h = float(h_totals[peak_idx])
        peak_day_relative[cap_l_idx, t_start_idx] = peak_time
        peak_bed_pct[cap_l_idx, t_start_idx] = (
            100.0 * peak_h / metric_meta.available_beds
        )

    default_x = _find_value_index(
        [float(v) for v in metric_meta.t_start_vals],
        metric_meta.default_t_start,
    )
    default_y = _find_value_index(
        [float(v) for v in metric_meta.cap_l_vals],
        metric_meta.default_cap_l,
    )
    if default_x is None or default_y is None:
        msg = "Default t_start/cap_l is not on scenario grid"
        raise ValueError(msg)

    baseline = burden[default_y, default_x]
    if baseline <= 0:
        msg = f"Non-positive panel baseline in {results_dir}: {baseline}"
        raise ValueError(msg)

    return PanelMetrics(
        burden_pct_change=(burden / baseline - 1.0) * 100.0,
        peak_day_relative=peak_day_relative,
        peak_bed_pct=peak_bed_pct,
    )


def _run_panel_simulation(
    base_cfg: dict[str, Any],
    cfg_path: Path,
    out_dir: Path,
    r0_value: float,
    s_frac: float,
) -> None:
    """Run one t_start x cap_l panel into an isolated output directory."""
    cfg = copy.deepcopy(base_cfg)

    n0 = float(cfg["parameter"]["n0"]["value"])
    i0_total = sum(
        float(v["value"])
        for k, v in cfg["parameter"].items()
        if k.startswith("i0__vax_")
    )
    h0_total = sum(
        float(v["value"])
        for k, v in cfg["parameter"].items()
        if k.startswith("h0__vax_")
    )
    s0_non_u = sum(
        float(v["value"])
        for k, v in cfg["parameter"].items()
        if k.startswith("s0__vax_") and k != "s0__vax_u"
    )
    r0_non_u = sum(
        float(v["value"])
        for k, v in cfg["parameter"].items()
        if k.startswith("r0__vax_") and k != "r0__vax_u"
    )

    s0 = s_frac * n0 - s0_non_u
    if s0 < 0:
        msg = f"Computed negative susceptible initial state for s_frac={s_frac}: {s0}"
        raise ValueError(msg)

    r0_init = n0 - s0 - s0_non_u - i0_total - h0_total - r0_non_u
    if r0_init < 0:
        msg = (
            f"Computed negative recovered initial state for s_frac={s_frac}: {r0_init}"
        )
        raise ValueError(msg)

    _set_param(cfg, "r0", r0_value)
    _set_param(cfg, "s0__vax_u", s0)
    _set_param(cfg, "r0__vax_u", r0_init)

    out_dir.mkdir(parents=True, exist_ok=True)
    _set_backend_root(cfg, str(out_dir))

    with tempfile.NamedTemporaryFile(
        "w", suffix=".yml", delete=False, encoding="utf-8"
    ) as tmp:
        yaml.safe_dump(cfg, tmp, sort_keys=False)
        tmp_cfg_path = Path(tmp.name)

    try:
        flepimop2_exe = shutil.which("flepimop2")
        if flepimop2_exe is None:
            msg = "flepimop2 executable not found in PATH"
            raise FileNotFoundError(msg)
        subprocess.run(  # noqa: S603
            [
                flepimop2_exe,
                "simulate",
                str(tmp_cfg_path),
                "-t",
                "scenario_sweep",
            ],
            check=True,
            cwd=cfg_path.parent.parent,
        )
    finally:
        tmp_cfg_path.unlink(missing_ok=True)


def _normalize_axes(
    axes: np.ndarray,
    n_rows: int,
    n_cols: int,
) -> np.ndarray:
    """Normalize matplotlib subplot axes to a 2D array."""
    if n_rows == 1 and n_cols == 1:
        return np.array([[axes]])
    if n_rows == 1:
        return np.array([axes])
    if n_cols == 1:
        return np.array([[ax] for ax in axes])
    return axes


def _metric_matrix(panel_metrics: PanelMetrics, metric: MetricName) -> np.ndarray:
    """Select the metric matrix for plotting."""
    if metric == "burden":
        return panel_metrics.burden_pct_change
    if metric == "peak_day":
        return panel_metrics.peak_day_relative
    return panel_metrics.peak_bed_pct


def _annotation_text(metric: MetricName, value: float) -> str:
    """Format per-cell annotation text for each metric."""
    if metric == "burden":
        return f"{round(value):+d}%"
    if metric == "peak_day":
        return f"d{round(value):d}"
    # peak_bed_pct: use integer when ≥100 to prevent cell overflow
    if abs(value) >= _BED_PCT_INTEGER_THRESHOLD:
        return f"{round(value):d}%"
    return f"{value:.1f}%"


def _draw_panel(
    ax: Axes,
    values: np.ndarray,
    panel_meta: PanelDrawMeta,
    figure_spec: FigureSpec,
) -> None:
    """Draw one panel with shared global color limits from figure_spec."""
    vmin = figure_spec.vmin
    vmax = figure_spec.vmax

    ax.imshow(
        values,
        cmap=figure_spec.cmap,
        aspect="auto",
        origin="lower",
        vmin=vmin,
        vmax=vmax,
    )

    for i in range(len(panel_meta.cap_l_vals)):
        for j in range(len(panel_meta.t_start_vals)):
            if (
                panel_meta.default_x is not None
                and panel_meta.default_y is not None
                and i == panel_meta.default_y
                and j == panel_meta.default_x
            ):
                continue
            val = float(values[i, j])
            threshold = 0.35 * max(abs(vmin), abs(vmax), 1.0)
            text_color = "black" if abs(val) < threshold else "white"
            ax.text(
                j,
                i,
                _annotation_text(figure_spec.metric, val),
                ha="center",
                va="center",
                color=text_color,
                fontsize=5.5,
                fontweight="bold",
            )

    if panel_meta.default_x is not None and panel_meta.default_y is not None:
        ax.add_patch(
            mpatches.Rectangle(
                (panel_meta.default_x - 0.5, panel_meta.default_y - 0.5),
                1.0,
                1.0,
                fill=False,
                edgecolor="black",
                linewidth=2.0,
            ),
        )

    if panel_meta.show_title:
        ax.set_title(f"R0={panel_meta.r0_val:.1f}", fontsize=12, fontweight="bold")

    ax.set_xticks(range(len(panel_meta.t_start_vals)))
    ax.set_xticklabels([str(int(v)) for v in panel_meta.t_start_vals], fontsize=8)
    ax.set_yticks(range(len(panel_meta.cap_l_vals)))
    ax.set_yticklabels([f"{v:.2f}" for v in panel_meta.cap_l_vals], fontsize=8)

    if panel_meta.show_row_label:
        ax.text(
            -0.35,
            0.5,
            f"S0={round(panel_meta.s_frac * 100)}%",
            transform=ax.transAxes,
            ha="right",
            va="center",
            fontsize=11,
            fontweight="bold",
        )
        ax.set_ylabel("Vaccine Coverage Cap")

    if panel_meta.show_xlabel:
        ax.set_xlabel("Campaign Start Time (days)")


def _make_panel_figure(
    panel_data: dict[tuple[float, float], PanelMetrics],
    plot_meta: PlotMeta,
    figure_spec: FigureSpec,
) -> None:
    """Render one metric figure as a 3x3 panel plot with a shared global color scale."""
    # Compute global vmin/vmax across all panels so the shared colorbar is accurate.
    all_values = [_metric_matrix(pm, figure_spec.metric) for pm in panel_data.values()]
    if figure_spec.symmetric_about_zero:
        global_abs_max = max(
            1.0,
            float(math.ceil(max(float(np.abs(v).max()) for v in all_values))),
        )
        spec = dataclasses.replace(
            figure_spec, vmin=-global_abs_max, vmax=global_abs_max
        )
    else:
        global_min = float(min(float(v.min()) for v in all_values))
        global_max = float(max(float(v.max()) for v in all_values))
        if global_min == global_max:
            global_min -= 0.5
            global_max += 0.5
        spec = dataclasses.replace(figure_spec, vmin=global_min, vmax=global_max)
    fig, axes = plt.subplots(
        nrows=len(plot_meta.s_frac_values),
        ncols=len(plot_meta.r0_values),
        figsize=(16, 12),
        sharex=True,
        sharey=True,
    )

    axes = _normalize_axes(axes, len(plot_meta.s_frac_values), len(plot_meta.r0_values))

    default_x = _find_value_index(
        [float(v) for v in plot_meta.t_start_vals],
        plot_meta.default_t_start,
    )
    default_y = _find_value_index(
        [float(v) for v in plot_meta.cap_l_vals],
        plot_meta.default_cap_l,
    )

    for row, s_frac in enumerate(plot_meta.s_frac_values):
        for col, r0_val in enumerate(plot_meta.r0_values):
            panel_metrics = panel_data[r0_val, s_frac]
            values = _metric_matrix(panel_metrics, spec.metric)
            panel_meta = PanelDrawMeta(
                r0_val=r0_val,
                s_frac=s_frac,
                show_title=row == 0,
                show_row_label=col == 0,
                show_xlabel=row == len(plot_meta.s_frac_values) - 1,
                t_start_vals=plot_meta.t_start_vals,
                cap_l_vals=plot_meta.cap_l_vals,
                default_x=default_x,
                default_y=default_y,
            )
            _draw_panel(axes[row, col], values, panel_meta, spec)

    fig.subplots_adjust(
        left=0.16,
        right=0.95,
        bottom=0.08,
        top=0.90,
        wspace=0.09,
        hspace=0.06,
    )

    fig.suptitle(spec.title, fontsize=14, fontweight="bold")

    norm = colors.Normalize(vmin=spec.vmin, vmax=spec.vmax)
    sm = cm.ScalarMappable(cmap=spec.cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes.ravel().tolist(), shrink=0.8, pad=0.02)
    cbar.set_label(spec.cbar_label, fontsize=11, fontweight="bold")

    spec.output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(spec.output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _parse_cli_args(
    args: list[str],
) -> tuple[Path, Path, Path | None, Path | None, bool, bool]:
    """Parse CLI args and return normalized paths/flags."""
    if len(args) < ARG_LEN_MIN:
        msg = (
            "python postprocessing/scenario_heatmap_3x3_legacy.py "
            "<config.yml> <burden.png> [<peak_day.png> <peak_bed_pct.png>] "
            "[--run] [--burden-only]"
        )
        raise SystemExit(msg)

    run_simulations = "--run" in args
    burden_only = "--burden-only" in args
    positional = [a for a in args if a not in {"--run", "--burden-only"}]

    if burden_only and len(positional) != EXPECTED_POSITIONAL_BURDEN_ONLY:
        msg = (
            "With --burden-only, expected: "
            "<config.yml> <burden.png> [--run] [--burden-only]"
        )
        raise SystemExit(msg)
    if (not burden_only) and len(positional) != EXPECTED_POSITIONAL_ALL_METRICS:
        msg = (
            "Without --burden-only, expected: "
            "<config.yml> <burden.png> <peak_day.png> <peak_bed_pct.png> [--run]"
        )
        raise SystemExit(msg)

    cfg_path = Path(positional[0])
    burden_out = Path(positional[1])
    peak_day_out = Path(positional[2]) if not burden_only else None
    peak_bed_pct_out = Path(positional[3]) if not burden_only else None
    return (
        cfg_path,
        burden_out,
        peak_day_out,
        peak_bed_pct_out,
        run_simulations,
        burden_only,
    )


def main() -> None:  # noqa: PLR0914
    """Run panel simulations (optional) and render legacy panel figures."""
    (
        cfg_path,
        burden_out,
        peak_day_out,
        peak_bed_pct_out,
        run_simulations,
        burden_only,
    ) = _parse_cli_args(sys.argv[1:])

    with cfg_path.open(encoding="utf-8") as f:
        raw_cfg = yaml.safe_load(f)

    config_model = ConfigurationModel.from_yaml(cfg_path)
    t_start_vals = _scenario_param_values(raw_cfg, SWEEP_SCENARIO_NAME, "t_start")
    cap_l_vals = _scenario_param_values(raw_cfg, SWEEP_SCENARIO_NAME, "cap_l")
    r0_values = _scenario_param_values(raw_cfg, PANEL_SCENARIO_NAME, "r0")
    s_frac_values = _scenario_param_values(raw_cfg, PANEL_SCENARIO_NAME, "s_frac")

    default_t_start = float(cast("Any", config_model.parameters["t_start"]).value)
    default_cap_l = float(cast("Any", config_model.parameters["cap_l"]).value)
    n0 = float(cast("Any", config_model.parameters["n0"]).value)
    available_beds = (BEDS_PER_1000 / 1000.0) * n0

    base_root = Path("model_output") / "legacy_r0_s0_batches"
    panel_data: dict[tuple[float, float], PanelMetrics] = {}
    panel_metric_meta = PanelMetricMeta(
        t_start_vals=t_start_vals,
        cap_l_vals=cap_l_vals,
        default_t_start=default_t_start,
        default_cap_l=default_cap_l,
        available_beds=available_beds,
    )

    if run_simulations:
        with cfg_path.open(encoding="utf-8") as f:
            base_cfg = yaml.safe_load(f)

        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        batch_root = base_root / stamp
        batch_root.mkdir(parents=True, exist_ok=True)

        for r0_val in r0_values:
            for s_frac in s_frac_values:
                panel_dir = batch_root / (
                    f"r0_{_slug_float(r0_val)}__sfrac_{_slug_float(s_frac)}"
                )
                LOGGER.info(
                    "Running legacy panel simulation: R0=%.1f, S0=%.1f%% -> %s",
                    r0_val,
                    s_frac * 100.0,
                    panel_dir,
                )
                _run_panel_simulation(base_cfg, cfg_path, panel_dir, r0_val, s_frac)
                panel_data[r0_val, s_frac] = _extract_panel_metrics(
                    panel_dir,
                    panel_metric_meta,
                )

        latest_txt = base_root / "LATEST"
        latest_txt.write_text(stamp, encoding="utf-8")
    else:
        latest_txt = base_root / "LATEST"
        if not latest_txt.exists():
            msg = (
                "No batch marker found. Run with --run once to generate panel outputs."
            )
            raise FileNotFoundError(msg)
        stamp = latest_txt.read_text().strip()
        batch_root = base_root / stamp

        for r0_val in r0_values:
            for s_frac in s_frac_values:
                panel_dir = batch_root / (
                    f"r0_{_slug_float(r0_val)}__sfrac_{_slug_float(s_frac)}"
                )
                panel_data[r0_val, s_frac] = _extract_panel_metrics(
                    panel_dir,
                    panel_metric_meta,
                )

    plot_meta = PlotMeta(
        t_start_vals=t_start_vals,
        cap_l_vals=cap_l_vals,
        r0_values=r0_values,
        s_frac_values=s_frac_values,
        default_t_start=default_t_start,
        default_cap_l=default_cap_l,
    )

    figure_specs = [
        FigureSpec(
            metric="burden",
            title=(
                "Hospitalization Burden Across Vaccination Policy by R0 and "
                "Initial Susceptible Share\n"
                f"Panel baseline: t_start={default_t_start:g}, cap_l={default_cap_l:g}"
            ),
            cbar_label="% Change from Baseline",
            cmap="RdYlGn_r",
            symmetric_about_zero=True,
            output_path=burden_out,
        ),
    ]

    if not burden_only and peak_day_out is not None and peak_bed_pct_out is not None:
        figure_specs.extend([
            FigureSpec(
                metric="peak_day",
                title=(
                    "Peak Hospitalization Day (from Simulation Start) by R0 and "
                    "Initial Susceptible Share"
                ),
                cbar_label="Day of Peak Hospitalization (from Simulation Start)",
                cmap="YlOrRd",
                symmetric_about_zero=False,
                output_path=peak_day_out,
            ),
            FigureSpec(
                metric="peak_bed_pct",
                title=(
                    "Peak Hospital Occupancy as % of Available Beds by R0 and "
                    "Initial Susceptible Share"
                ),
                cbar_label="Peak Hospital Occupancy (% of Available Beds)",
                cmap="YlOrRd",
                symmetric_about_zero=False,
                output_path=peak_bed_pct_out,
            ),
        ])

    for spec in figure_specs:
        _make_panel_figure(panel_data, plot_meta, spec)
        sys.stdout.write(f"Saved {spec.metric} figure to {spec.output_path}\n")


if __name__ == "__main__":
    main()
