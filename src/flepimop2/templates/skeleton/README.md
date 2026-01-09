# My Project

## Getting Started

1. Start by creating a conda environment for the project using `just venv`. To do this you will need to have the [`just` task runner](https://just.systems/) and [`conda` environment manager](https://conda.org/) installed. You can also choose to use a different task runner, like `make`, or environment manager, like `uv`, at this stage if you wish.
2. If this is your first time using `flepimop2` please follow the tutorial provided in the [`flepimop2-demo` repository](https://github.com/ACCIDDA/flepimop2-demo) replacing the `configs/EDITME.yaml` example configuration file with the `configs/SIR_script.yaml` from the demo repository.
3. If this is not your first project using `flepimop2` then feel free to update the `environment.yaml` file with other dependencies required for your project as well as updating the `configs/EDITME.yaml` example configuration file with your configuration file.

## Skelton Directory Structure

```shell
./
├── configs/
│   ├── built/
│   └── EDITME.yaml
├── environment.yaml
├── justfile
├── model_input/
│   ├── data/
│   └── plugins/
├── model_output/
└── README.md

7 directories, 4 files
```

- The `configs/` directory is the place to keep configuration files. As a starting point the `configs/EDITME.yaml` configuration has been placed as an example to edit. The `configs/built/` directory is a gitignored directory for patched together configuration files.
- The `environment.yaml` file contains a conda environment configuration that can be used to define a reproducible conda environment containing python/R dependencies that can be shared. By default the only dependency contained in this file right now is `flepimop2` itself.
- The `justfile` contains recipe definitions for `just`. Currently the only recipe defined is for creating a conda environment from the `environment.yaml` file, but this can be extended to automate series of `flepimop2` commands together.
- The `model_input/` directory is the place for model inputs which are broadly split into `model_input/data/` for raw input data (e.g. CSV of hospitalizations, parquet of vaccinations, etc.) and `model_input/plugins/` for one of scripts that can be loaded by `flepimop2`. Users should add more subdirectories here as needed for more distinct types of inputs.
- The `model_output/` directory is a gitignored directory that is the general purposes location for model outputs.
