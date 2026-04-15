# Welcome to `flepimop2`

The next generation of the flexible epidemic modeling pipeline.

## What is `flepimop2`?

`flepimop2` is a Python package and command-line tool for running epidemic simulations. It works with configuration files to define and execute analysis pipelines. Because it is also a library, you can write custom analyses that read and write data in a way that works seamlessly with the rest of the pipeline, and advanced users can develop shareable modules that plug directly into it.

At the core of flepimop2 is a modular design that separates three concerns:

- **System**: the mathematical model describing how disease spreads (e.g., a compartmental SIR model)
- **Engine**: the numerical solver that runs the model forward in time
- **Backend**: the output format for saving results

Each of these is defined independently and referenced in a single YAML configuration file. Because the full pipeline — model, solver, parameters, time grid, and post-processing — lives in one file, workflows are reproducible, version-controllable, and easy to share with collaborators.

## Prerequisites

Make sure the following are available on your system before getting started:

- [git](https://git-scm.com/install/) — for cloning the repository
- [pipx](https://pipx.pypa.io/latest/installation/) — for installing the CLI
- [just](https://just.systems/man/en/packages.html) — task runner used to set up project environments
- [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) (or [mamba](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html)) — for managing project virtual environments

## Installation

Clone the flepimop2 repository and install the CLI with pipx:

```bash
git clone git@github.com:ACCIDDA/flepimop2.git
cd flepimop2
pipx install .
```

This makes the `flepimop2` command available globally so you can use it from any project directory.

## Create a Project

Navigate to wherever you want your projects to live, then run:

```bash
flepimop2 skeleton quick_start_project
cd quick_start_project
```

This creates a new directory and populates it with the standard project structure:

```
quick_start_project/
├── configs/
│   ├── built/
│   └── EDITME.yaml
├── environment.yaml
├── justfile
├── model_input/
│   ├── data/
│   └── plugins/
├── model_output/
└── README.md
```

Every flepimop2 project needs at least three things to run: a configuration file, a system, and an engine. The **configuration file** (saved in `configs`) is a YAML file that specifies your model parameters, which system and engine to use, where to write outputs, and optionally what post-processing steps to run after a simulation. The **system** and **engine** are backends that implement the model dynamics and the numerical solver, respectively. In this quickstart, we will use Python scripts (saved in `model_input/plugins`) for both the system and the engine.

For this quickstart, download the following files and add them to your project:

- [config.yaml](assets/quickstart_workflow/config.yaml) → save to `configs`
- [SIR.py](assets/quickstart_workflow/SIR.py) → save to `model_input/plugins`.
- [solve_ivp.py](assets/quickstart_workflow/solve_ivp.py) → save to `model_input/plugins`

??? example "Configuration File"
    ```yaml
    --8<-- "assets/quickstart_workflow/config.yaml"
    ```

??? example "SIR System"
    ```python
    --8<-- "assets/quickstart_workflow/SIR.py"
    ```

??? example "scipy ODE Engine"
    ```python
    --8<-- "assets/quickstart_workflow/solve_ivp.py"
    ```

Next, set up the project's virtual environment. The `environment.yaml` file in your project specifies its dependencies. The default skeleton includes flepimop2, but you will need to add `pip` and `scipy` to the dependency list before creating the environment. Copy the [environment.yaml](assets/quickstart_workflow/environment.yaml) file to your project, replacing the existing file. 

??? example "Environment YAML file"
    ```yaml
    --8<-- "assets/quickstart_workflow/environment.yaml"
    ```

Then create the environment:

```bash
just venv
```

## Simulate an Outbreak

Activate the project environment and run the simulation:

```bash
conda activate ./venv
flepimop2 simulate configs/config.yaml
```

Results are saved automatically to the `model_output` directory as a CSV file. As flepimop2 will only work when it is run in an appripriate environment, you will need to run `conda activate ./venv` each time you open a new terminal session before using `flepimop2`.

## Adding Post-Processing

flepimop2 supports post-processing steps that run after a simulation — useful for generating plots, rendering notebooks, or producing summary tables. Post-processing steps are defined in the `process` block of your configuration file and can invoke R scripts, Python scripts, or Jupyter notebooks.

You will need to create a `postprocessing` directory within your project:

```bash
mkdir postprocessing
```

The resources for the example post-processing pipeline are in the `assets/postprocessing_workflow` folder of the repository. You will need to copy them into your project as follows:

- [config.yaml](assets/postprocessing_workflow/config.yaml) → `configs/config.yaml` (replaces the quickstart config)
- [SIR_plot.R](assets/postprocessing_workflow/SIR_plot.R) → `postprocessing/SIR_plot.R`
- [SirPlot.ipynb](assets/postprocessing_workflow/SirPlot.ipynb) → `postprocessing/SirPlot.ipynb`

After copying the files, your project structure should look like this:

```
quick_start_project/
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
│   ├── SIR_plot.R
│   └── SirPlot.ipynb
└── README.md
```

The post-processing workflow requires additional R and Python dependencies. Replace your `environment.yaml` with the one from [assets/postprocessing_workflow/environment.yaml](assets/postprocessing_workflow/environment.yaml), then recreate the environment (this can be done by restarting your terminal and removing the existing venv folder, then running the following):

```bash
just venv
conda activate ./venv
```

Take a look at the updated `configs/config.yaml`. It defines two simulation targets — `demo` and `hires` — that share the same model parameters but use different time resolutions. A separate post-processing pipeline is defined for each target under the `process` block. flepimop2 defaults to the first defined target, but you can select a specific one with `--target`:

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

## Contributing

To contribute to the main `flepimop2` pipeline, visit us [on GitHub](https://github.com/ACCIDDA/flepimop2).

## Site Development

This site uses [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/), a theme for [MkDocs](https://www.mkdocs.org/).

To launch the site in developer mode, navigate to the `flepimop2` repo and run:

```bash
just serve
```
