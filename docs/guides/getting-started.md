# Getting Started

This guide walks through flepimop2's more advanced features. We describe the system-engine architecture, then show how to use that for model specification and solver configuration. We show those elements flow into simulation setup and then post-processing. It is intended for users who have already worked through the [quickstart guide](../index.md) and are ready to explore the framework in more depth.

## Prerequisites

Make sure the following are available on your system:

- [git](https://git-scm.com/install/)
- [pipx](https://pipx.pypa.io/latest/installation/)
- [just](https://just.systems/man/en/packages.html)
- [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) (or [mamba](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html))

## Installation

```bash
pipx install flepimop2
```

## Create a Project

Switch from the flepimop2 clone repository to the directory you want to conduct your analysis in. Once there, run the following command:

```bash
flepimop2 skeleton full_start_project
cd full_start_project
```

Within the project you have created, replace the default `environment.yaml` with the one from [assets/full_feature_workflow/environment.yaml](../assets/full_feature_workflow/environment.yaml), which includes the additional dependencies required for this guide. Then create and activate the environment:

```bash
just venv
conda activate ./venv
```

---

## The System-Engine Architecture

flepimop2 separates the specification of a model from the computation that runs it. A **system** defines what happens — the equations governing state transitions. An **engine** defines how those equations are solved — the numerical method and its configuration. These two components are independently specified in the config file and can be swapped in any combination.

This separation matters in practice. A disease modeler can publish a system — the compartmental structure and transmission logic — without prescribing a solver. Collaborators can then run that same system with a different engine suited to their performance requirements or numerical preferences, without ever touching the model code.

### The Wrapper Pattern

The quickstart guide demonstrates the simplest case: both the system and engine are user-provided Python scripts loaded at runtime.

```yaml
system:
  - module: wrapper
    state_change: flow
    script: model_input/plugins/SIR.py

engine:
  - module: wrapper
    state_change: flow
    script: model_input/plugins/solve_ivp.py
```

The `wrapper` module dynamically imports the script (path defined in the `script` argument) and looks for a required entry point function: `stepper()` for systems, `runner()` for engines. The `state_change` field tells flepimop2 what the stepper returns — `flow` means dY/dt (derivatives suitable for ODE integration), `delta` means ΔY (increments), and `state` means the full new state vector.

### Swapping Solvers Without Changing the Model

Because the system and engine are decoupled, changing the solver requires only a change to the config file. The following two configurations run the same `SIR.py` model but use different engines:

**With the wrapper engine (scipy)**:
```yaml
system:
  - module: wrapper
    state_change: flow
    script: model_input/plugins/SIR.py

engine:
  - module: wrapper
    state_change: flow
    script: model_input/plugins/solve_ivp.py
```

**With op_engine (swapping only the engine block)**:
```yaml
system:
  - module: wrapper
    state_change: flow
    script: model_input/plugins/SIR.py

engine:
  - module: op_engine
    config:
      method: heun
      adaptive: false
      rtol: 1.0e-6
      atol: 1.0e-9
```

`SIR.py` is untouched. The only difference is the `engine` block. This makes it straightforward to benchmark solvers against each other, validate results across implementations, or switch to a faster solver once a model has been validated.

---

## Defining Models Directly in YAML (op_system)

For users who prefer not to write Python, the `op_system` module (from the `flepimop2-op-system` package) allows compartmental models to be specified entirely within the config file using symbolic expressions.

```yaml
system:
  - module: op_system
    spec:
      kind: expr
      state: [S, I, R]
      equations:
        S: -beta * S * I / sum_state()
        I: beta * S * I / sum_state() - gamma * I
        R: gamma * I
      initial_state:
        S: s0
        I: i0
        R: r0
```

The example above specifies a basic SIR model. `kind: expr` indicates dY/dt expressions will be provided for each compartment. The compartments are listed in the `state` field, and their corresponding dY/dt expressions are defined in `equations`. The `sum_state()` helper evaluates to the total population at each time step — equivalent to `S + I + R` — and is provided to make density-dependent transmission terms concise and readable. Symbolic representations for the initial states of each of these compartments are defined in `initial_state`; each of these symbolic representations are then assigned a numeric value in `parameters` later in the file.

If a user wants to defines disease system by specifying the transitions between states instead of the expression for each state, they can do so as follows:

```yaml
system:
  - module: op_system
    spec:
      kind: transitions
      state: [S, I, R]
      transitions:
        - from: S
          to: I
          rate: beta * I / sum_state()
        - from: I
          to: R
          rate: gamma
```

When using `op_system`, no `state_change` field is required; the module infers it from the symbolic specification. `op_system` requires `op_engine` — the symbolic expression compiler and solver are designed to work together.

---

## Simulation Targets and Time Specifications

### Defining Multiple Targets

A single configuration file can define multiple named simulation targets under the `simulate` block. Each target can have its own time grid, and can independently reference any named system, engine, or backend defined elsewhere in the config:

```yaml
simulate:
  demo:
    times: [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
  hires:
    times: 0.0:0.1:100.0
```

flepimop2 defaults to the first defined target when none is specified. To run a specific target:

```bash
flepimop2 simulate configs/SIR_script.yml
flepimop2 simulate --target hires configs/SIR_script.yml
```

Multiple targets in a single config are useful for running quick sanity checks at coarse resolution alongside production runs at fine resolution, without maintaining separate config files.

### Time Specification Syntax

The `times` field supports two formats:

**Explicit list**: Time points are specified directly. Useful when evaluation times are irregular or correspond to observation times:

```yaml
times: [0, 7, 14, 21, 28, 60, 90, 180, 365]
```

**Range shorthand**: A compact `start:step:stop` notation generates a uniformly spaced grid.

```yaml
times: 0.0:0.1:100.0   # 1001 time points from 0 to 100, inclusive
times: 0.0:1.0:365.0   # daily steps over one year
```

The range syntax is particularly convenient for high-resolution runs where listing every time point by hand would be impractical.

---

## Post-Processing

Post-processing steps are defined in the `process` block and are executed by `flepimop2 process`. Each named entry under `process` specifies a module type and the arguments needed to run it. Like simulation targets, process targets can be run selectively with `--target`. These post-processing steps will often require accompanying scripts; ensure these scripts have been saved in the file paths specified in the `command` argument.

### Shell Processes

The `shell` module runs an arbitrary command-line program. This is the standard way to invoke R scripts or standalone Python scripts:

```yaml
process:
  plot_demo:
    module: shell
    command: python postprocessing/SIR_plot_op_engine.py
    args:
      - configs/config.yml
      - model_output/SIR_plot_op_engine.png
```

The `command` field is the executable, and `args` is a list of positional arguments passed to it. The working directory is the project root.

R scripts work the same way:

```yaml
process:
  r_plot:
    module: shell
    command: Rscript postprocessing/SIR_plot.R
    args:
      - configs/config.yml
      - model_output/SIR_plot.png
```

Any shell command is valid here — the module imposes no restrictions on what runs. Exit codes are checked; a non-zero exit will raise an error and halt the pipeline.

### Jupyter Notebook Rendering (ipynbrender)

The `ipynbrender` module executes a Jupyter notebook and renders the output to HTML:

```yaml
process:
  notebook:
    module: ipynbrender
    file: postprocessing/SirPlot.ipynb
    output: model_output/SirPlot.html
```

`ipynbrender` requires the `flepimop2-ipynbrender` adapter package (included in the full-feature `environment.yaml`). The notebook is executed in place and a self-contained HTML file is written to the `output` path. This is useful for producing reports that include inline figures and narrative text alongside simulation outputs.

### Multiple Process Targets

Multiple named process targets can coexist in a single config:

```yaml
process:
  r_plot:
    module: shell
    command: Rscript postprocessing/SIR_plot.R
    args:
      - configs/config.yml
      - model_output/SIR_plot.png
  python_plot:
    module: shell
    command: python postprocessing/SIR_plot_op_engine.py
    args:
      - configs/config.yml
      - model_output/SIR_plot_py.png
  notebook:
    module: ipynbrender
    file: postprocessing/SirPlot.ipynb
    output: model_output/SirPlot.html
```

Running `flepimop2 process configs/config.yml` executes the first defined target. To run a specific one:

```bash
flepimop2 process --target notebook configs/config.yml
```

### Accessing Config Programmatically in Post-Processing Scripts

Python post-processing scripts can use flepimop2's public configuration API to locate output files without hardcoding paths. `ConfigurationModel.from_yaml()` returns a fully validated, typed representation of the config, from which the backend's output directory can be resolved:

<!-- skip: next -->
```python
from flepimop2.configuration import ConfigurationModel
from pathlib import Path

config_model = ConfigurationModel.from_yaml(Path("configs/config.yml"))

# Get the backend used by the first simulate target
first_sim = next(iter(config_model.simulate.values()))
backend_name = getattr(first_sim, "backend", None) or "default"
backend_cfg = config_model.backends[backend_name].model_dump()
results_dir = Path(backend_cfg.get("root") or "model_output")

# Find the most recently modified CSV
latest_csv = sorted(results_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime)[-1]
```

This pattern means post-processing scripts adapt automatically when the backend or output directory changes in the config — no manual path updates required.

---

## Full Project Setup

The files for this walkthrough are in `assets/full_feature_workflow/` in the flepimop2 repository.

### File Layout

Create a `postprocessing/` directory in your project.

```bash
mkdir postprocessing
```

Copy the following:

- [config.yml](../assets/full_feature_workflow/config.yml) → `configs/config.yml`
- [SIR_plot.R](../assets/full_feature_workflow/SIR_plot.R) → `postprocessing/SIR_plot.R`
- [SirPlot.ipynb](../assets/full_feature_workflow/SirPlot.ipynb) → `postprocessing/SirPlot.ipynb`
- [SIR_plot_op_engine.py](../assets/full_feature_workflow/SIR_plot_op_engine.py) → `postprocessing/SIR_plot_op_engine.py`

Your project layout should look like this:

```
full_start_project/
├── configs/
│   ├── built/
│   ├── config.yml
│   └── EDITME.yaml
├── environment.yaml
├── justfile
├── model_input/
│   ├── data/
│   └── plugins/
├── model_output/
├── postprocessing/
│   ├── SIR_plot.R
│   ├── SIR_plot_op_engine.py
│   └── SirPlot.ipynb
└── README.md
```

### The Configuration File

??? example "config.yml"
    ```yaml
    --8<-- "assets/full_feature_workflow/config.yml"
    ```

Note that this config uses `op_system` and `op_engine` — no Python plugin scripts are needed for the model or solver. The `model_input/plugins` directory can remain empty.

### Running the Pipeline

```bash
# Run the default (demo) simulation target
flepimop2 simulate configs/config.yml

# Run the high-resolution target
flepimop2 simulate --target hires configs/config.yml

# Run post-processing for the default target
flepimop2 process configs/config.yml

# Run post-processing for the r_plot target
flepimop2 process --target r_plot configs/config.yml
```

Simulation outputs are written to `model_output` as CSV files. Post-processing outputs (plots, rendered notebooks) are also written there, with filenames as specified in the `process` block.
