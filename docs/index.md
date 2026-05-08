# Welcome to `flepimop2`

The next generation of the flexible epidemic modeling pipeline.

## What is `flepimop2`?

`flepimop2` is a Python package and command-line tool for running dynamic system simulations. It works with configuration files to define and execute analysis pipelines. Because it is also a library, you can write custom analyses that read and write data in a way that works seamlessly with the rest of the pipeline, and advanced users can develop shareable modules that plug directly into it.

At the core of flepimop2 is a modular design that separates three concerns:

- **System**: the mathematical model describing how the dynamical system evolves (e.g., disease spreads with a compartmental SIR model)
- **Engine**: the numerical solver that runs the model forward in time
- **Backend**: the output format for saving results

Each of these is defined independently and referenced in a single YAML configuration file. Because the full pipeline — model, solver, parameters, time grid, and post-processing — lives in one file, workflows are reproducible, version-controllable, and easy to share with collaborators.

## Installation
`flepimop2` is published on [PyPI](https://pypi.org/project/flepimop2/) and can be installed with `pip`:

```bash
pip install flepimop2
```

This makes the `flepimop2` command available globally so you can use it from any project directory.
If you want to work from a local clone instead, see the [installation guide](guides/install.md) for a source install and dependency setup.

## Create a Project

Download [quickstart-project.zip](downloads/quickstart-project.zip), unzip it wherever you want your project to live, then run:

```bash
unzip quickstart-project.zip
cd quickstart-project
```

The bundle already contains the standard project structure created by `flepimop2 skeleton`:

```
quickstart-project/
├── configs/
│   ├── built/
│   ├── config.yaml
│   └── EDITME.yaml
├── environment.yaml
├── justfile
├── model_input/
│   ├── data/
│   └── plugins/
├── model_output/
├── postprocessing/
│   └── SIR_plot.R
└── README.md
```

Every flepimop2 project needs at least three things to run: a configuration file, a system, and an engine. The **configuration file** (saved in `configs`) is a YAML file that specifies your model parameters, which system and engine to use, where to write outputs, and optionally what post-processing steps to run after a simulation. The **system** and **engine** are backends that implement the model dynamics and the numerical solver, respectively. In this quickstart, we will use Python scripts (saved in `model_input/plugins`) for both the system and the engine. The ZIP bundle above already places those files in the correct locations, includes the dependencies required for this page, and includes the post-processing script used later in the guide.

??? example "Configuration File"
    ```yaml
    --8<-- "assets/quickstart-project/configs/config.yaml"
    ```

??? example "SIR System"
    ```python
    --8<-- "assets/quickstart-project/model_input/plugins/SIR.py"
    ```

??? example "scipy ODE Engine"
    ```python
    --8<-- "assets/quickstart-project/model_input/plugins/solve_ivp.py"
    ```

Next, set up the project's virtual environment. The bundled `environment.yaml` already includes the dependencies required for this guide.

??? example "Environment YAML file"
    ```yaml
    --8<-- "assets/quickstart-project/environment.yaml"
    ```

Then create the environment:

```bash
just venv
conda activate ./venv
```

As flepimop2 will only work when it is run in an appropriate environment, you will need to run `conda activate ./venv` each time you open a new terminal session before using `flepimop2`.

## Simulate an Outbreak

Activate the project environment and run the simulation:

```bash
flepimop2 simulate configs/config.yaml
```

Results are saved automatically to the `model_output` directory as a CSV file. 

## Adding Post-Processing

flepimop2 supports post-processing steps that run after a simulation — useful for generating plots, rendering notebooks, or producing summary tables. Post-processing steps are defined in the `process` block of your configuration file and can invoke R scripts, Python scripts, or Jupyter notebooks.

The same `quickstart-project.zip` bundle already includes the post-processing config, script, and dependencies needed for this section.

The bundled project includes this post-processing file layout:

```
quickstart-project/
├── configs/
│   ├── built/
│   ├── config.yaml
│   └── EDITME.yaml
├── environment.yaml
├── justfile
├── model_input/
│   ├── data/
│   └── plugins/
│       ├── SIR.py
│       └── solve_ivp.py
├── model_output/
├── postprocessing/
│   └── SIR_plot.R
└── README.md
```

Take a look at `configs/config.yaml`. It defines two simulation targets — `demo` and `hires` — that share the same model parameters but use different time resolutions. A separate post-processing pipeline is defined for each target under the `process` block. flepimop2 defaults to the first defined target, but you can select a specific one with `--target`:

```bash
# Run the default (demo) target
flepimop2 simulate configs/config.yaml

# Run the high-resolution target instead
flepimop2 simulate --target hires configs/config.yaml
```

To run post-processing after a simulation, call `process` with the same config:

```bash
flepimop2 simulate configs/config.yaml
flepimop2 process configs/config.yaml
```

This runs the post-processing steps defined for the `demo` target, producing a plot. You can call post-processing for a specific plot with the same --target argument as you use for simulations.

```bash
flepimop2 simulate --target hires configs/config.yaml
flepimop2 process --target hires configs/config.yaml
```
