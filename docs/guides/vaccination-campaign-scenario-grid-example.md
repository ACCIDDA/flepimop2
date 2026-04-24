# Vaccination Campaign Scenario Grid Example

This guide walks through a policy-sweep SIRHD model with vaccination strata, and shows how to set up the configuration and figure-generation workflow in `flepimop2`.

## 1. Start from a New Repository

Create a fresh repo and scaffold the project skeleton:

```bash
mkdir vaccination-campaign-scenario-grid
cd vaccination-campaign-scenario-grid
git init
flepimop2 skeleton .
```

You will now have the standard `flepimop2` folder structure (`configs`, `model_input`, `postprocessing`, `model_output`, etc.) and can start adding your model-specific files.

## 2. Get the Example Config and Plot Scripts

Use the copies included with this guide in `docs/examples/vaccination-campaign-scenario-grid`:

- Config source:
  - `docs/examples/vaccination-campaign-scenario-grid/config/SIRHD_vax_scenario_grid.yml`
- Script sources:
  - `docs/examples/vaccination-campaign-scenario-grid/scripts/scenario_heatmap_3x3.py`
  - `docs/examples/vaccination-campaign-scenario-grid/scripts/scenario_spaghetti_incidence.py`
  - `docs/examples/vaccination-campaign-scenario-grid/scripts/scenario_peak_bed_summary.py`

Suggested placement in your new project:

- `configs/SIRHD_vax_scenario_grid.yml`
- `postprocessing/scenario_heatmap_3x3.py`
- `postprocessing/scenario_spaghetti_incidence.py`
- `postprocessing/scenario_peak_bed_summary.py`

## 3. Model Structure in `system`

At a high level, this model uses a vaccination axis (`u`, `v`, `w`) and state vectors per stratum for `S`, `I`, `H`, `R`, plus global `D`.

```yaml
system:
  - module: op_system
    state_change: flow
    spec:
      kind: transitions

      axes:
        - name: vax
          coords: [u, v, w]

      state:
        - S[vax]
        - I[vax]
        - H[vax]
        - R[vax]
        - D
```

Interpretation:
- `u`: unvaccinated
- `v`: vaccinated/protected
- `w`: vaccinated but waned protection

## 4. Aliases: Derived Terms and Rates

Aliases define reusable expressions and are often where model intent is most explicit.

```yaml
aliases:
  N: "sum_over(vax=j, S[vax=j] + I[vax=j] + H[vax=j] + R[vax=j])"
  lam: "(r0 / t_inf) * sum_over(vax=j, I[vax=j]) / N"
  rho_eff[vax]: "q[vax] * rho"
  delta_eff[vax]: "q[vax] * delta"
  pop[vax]: "S[vax] + I[vax] + H[vax] + R[vax]"
  coverage: "sum_over(vax=j IN [v, w], pop[vax=j]) / n0"
  rollout: "1.0 - np.exp(-ramp * np.maximum(0.0, t - t_start))"
  u: "np.maximum(0.0, k * (cap_l - coverage)) * rollout"
```

How to read this:
- `lam` is force of infection scaled by current infectious prevalence.
- `rho_eff[vax]` and `delta_eff[vax]` apply severity multipliers by vaccination stratum.
- `coverage` measures cumulative ever-vaccinated share (`v + w`).
- `u` is a dynamic campaign rate with two constraints:
  - starts after `t_start` (via `rollout`),
  - saturates as coverage approaches `cap_l`.

## 5. Transitions and Coordinate Shifts

The transition graph includes infection, progression, recovery, death, waning immunity, and vaccination movement between axis coordinates.

```yaml
transitions:
  - from: S[vax]
    to: I[vax]
    rate: lam

  - from: I[vax]
    to: H[vax]
    rate: rho_eff[vax] / t_inf
  - from: I[vax]
    to: R[vax]
    rate: (1 - rho_eff[vax]) / t_inf

  - from: H[vax]
    to: D
    rate: delta_eff[vax] / t_hosp
  - from: H[vax]
    to: R[vax]
    rate: (1 - delta_eff[vax]) / t_hosp

  - from: R[vax]
    to: S[vax]
    rate: alpha

  - coord_shift:
      vax: "u -> v"
    apply_to: [S, R]
    rate: u

  - coord_shift:
      vax: "v -> w"
    apply_to: [S, R]
    rate: omega
```

`coord_shift` is the key mechanism for axis-based state movement. Here:
- vaccination moves people from `u` to `v` in `S` and `R`,
- vaccine protection wanes from `v` to `w` in `S` and `R`.

## 6. Engine and Numerical Integration

```yaml
engine:
  - module: op_engine
    state_change: flow
    config:
      method: heun
      adaptive: true
      rtol: 1.0e-3
      atol: 1.0e-5
      dt_min: 1.0e-10
      dt_max: 2.0
      safety: 0.9
```

This uses adaptive Heun integration with bounded step sizes.

## 7. Scenario Axes and Policy Sweep

This config separates policy sweep axes from panel axes:

```yaml
scenarios:
  vax_campaign:
    module: grid
    parameters:
      t_start: [0, 7, 14, 21, 28, 35, 42, 49, 56, 63, 70]
      cap_l: [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]

  panel_grid:
    module: grid
    parameters:
      r0: [1.1, 2.0, 4.0]
      s_frac: [0.3, 0.5, 0.7]
```

Conceptually:
- `vax_campaign` spans policy levers (start timing and max coverage).
- `panel_grid` controls epidemiologic context (transmissibility and initial susceptible share).

## 8. Simulate, Backend, and Process Blocks

Simulation and output routing:

```yaml
simulate:
  scenario_sweep:
    times: "0.0:1.0:364.0"
    scenario: vax_campaign

backend:
  - module: csv
    root: model_output/SIRHD_vax
```

The three retained figure-generation targets:

```yaml
process:
  scenario_heatmap_3x3_run_batch_and_plot:
    module: shell
    command: python postprocessing/scenario_heatmap_3x3.py
    args:
      - configs/SIRHD_vax_scenario_grid.yml
      - model_output/plots/SIRHD_vax/SIRHD_vax_scenario_heatmap_3x3.png
      - --run
      - --burden-only

  scenario_spaghetti_incidence:
    module: shell
    command: python postprocessing/scenario_spaghetti_incidence.py
    args:
      - configs/SIRHD_vax_scenario_grid.yml
      - model_output/plots/SIRHD_vax/SIRHD_vax_spaghetti_incidence.png

  scenario_peak_bed_summary:
    module: shell
    command: python postprocessing/scenario_peak_bed_summary.py
    args:
      - configs/SIRHD_vax_scenario_grid.yml
      - model_output/plots/SIRHD_vax/SIRHD_vax_peak_bed_summary.png
```

## 9. Running the Example

From a working environment with `flepimop2` available:

```bash
flepimop2 simulate configs/SIRHD_vax_scenario_grid.yml -t scenario_sweep
flepimop2 process configs/SIRHD_vax_scenario_grid.yml -t scenario_heatmap_3x3_run_batch_and_plot
flepimop2 process configs/SIRHD_vax_scenario_grid.yml -t scenario_spaghetti_incidence
flepimop2 process configs/SIRHD_vax_scenario_grid.yml -t scenario_peak_bed_summary
```

## 10. Figure Interpretation

### 3x3 Policy Heatmap (Burden)

![3x3 burden heatmap](../examples/vaccination-campaign-scenario-grid/figures/SIRHD_vax_scenario_heatmap_3x3.png)

Use this to compare percent change in hospitalization burden across:
- rows/columns: epidemiologic context (`S0`, `R0`),
- heatmap axes: campaign start day vs coverage cap.

### 3x3 Weekly Incidence Trajectories

![3x3 weekly incidence spaghetti](../examples/vaccination-campaign-scenario-grid/figures/SIRHD_vax_spaghetti_incidence.png)

This emphasizes timing and shape of weekly admissions, with:
- color: campaign start day,
- linestyle: coverage cap.

### Peak Occupancy Summary (R0 Dominance)

![Peak occupancy summary](../examples/vaccination-campaign-scenario-grid/figures/SIRHD_vax_peak_bed_summary.png)

This view collapses policy combinations and highlights that changes in `R0` dominate variation in peak bed occupancy across the explored policy settings.

## 11. Complete Config Example

A complete copy of the example configuration used for this walkthrough is available at:

- `docs/examples/vaccination-campaign-scenario-grid/config/SIRHD_vax_scenario_grid.yml`
