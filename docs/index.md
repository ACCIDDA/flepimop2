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
flepimop2 skeleton quick_start_project
cd quick_start_project
```

This will create a new directory, `quick_start_project` and populate that directory with some files.

The most basic skeleton does not provide a system or engine, so you'll need to add these files:

??? example "Basic SIR Model"
    ```python
    some code
    ```

??? example "Basic scipy ODE Solver Engine"
    ```python
    more code
    ```

You'll also need to update the skeleton configuration file with these additions and set some parameters:

```yaml
some yaml content
```

### Simulate an Outbreak

Within the `quick_start_project` folder, 

## What is `flepimop`?

discussion
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