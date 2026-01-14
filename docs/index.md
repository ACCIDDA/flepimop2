# Welcome to `flepimop2`

The next generation of the flexible epidemic modeling pipeline.

## Quick Start

### Installation

You'll need [git](https://git-scm.com/install/) and [pipx](https://pipx.pypa.io/latest/installation/) on your system.

```bash
git clone git@github.com:ACCIDDA/flepimop2.git
cd flepimop2
pipx install .
```

This clones the source of the library, then uses it to install the application.

### Create a Project

Somewhere else on your system, run the command

```bash
flepimop2 skeleton quick_start_project -v
cd quick_start_project
```

This will create a new directory, `quick_start_project` and populate that directory with some files. The `-v` flag (for "verbose") will cause `skeleton` to also display the created directory structure.

The most basic skeleton does not provide a system or engine: you will need to specify those. Here is an example [SIR system](assets/SIR.py) and an example [ODE engine](assets/solve_ivp.py):

??? example "Basic SIR Model"
    ```python
    --8<-- "assets/SIR.py"
    ```

??? example "Basic scipy ODE Solver Engine"
    ```python
    --8<-- "assets/solve_ivp.py"
    ```

You'll also need to update the skeleton configuration file with these additions and set some parameters:

```yaml
system:
  - module: wrapper
    script: model_input/plugins/SIR.py

engine:
  - module: wrapper
    script: model_input/plugins/solve_ivp.py

parameter:
  beta:
    module: fixed
    value: 0.3
  gamma:
    module: fixed
    value: 0.1
  s0:
    module: fixed
    value: 999
  i0:
    module: fixed
    value: 1
  r0:
    module: fixed
    value: 0
```

### Simulate an Outbreak

Within the `quick_start_project` folder, you can now use `flepimop2` to run your model:

```bash
flepimop2 simulate configs/config.yaml
```

## What is `flepimop`?

The `flepimop` python package is a combined command line interface and library. The CLI application works with user commands and configuration files to execute analysis pipelines. Because `flepimop` is also a library, users can write their own flexible analyses leveraging that library to read and write data (and configuration information) in a way that "just works" with the pipeline. Additionally, advanced users can develop their own shareable modules that work with the pipeline.

illustration of analysis flow
illustration of how elements fit together

## Work with Us!

To contribute to the main `flepimop2` pipeline, you can join us [on github](https://github.com/ACCIDDA/flepimop2).

contact info, invitation to collaborate / contribute to repo

## Site Development

This site uses [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/), which is a theme for [MkDocs](https://www.mkdocs.org/).

To launch the site in developer mode, navigate to the `flepimop2` repo and then invoke at the command prompt:

```bash
just serve
```