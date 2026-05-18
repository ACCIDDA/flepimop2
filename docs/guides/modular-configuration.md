# Modular Configuration

This guide shows how to use `flepimop2 patch` to treat configuration files as composable building blocks. Users can apply the same pattern to many kinds of configuration variation:

- Keep stable parts of a workflow in one file,
- Keep interchangeable or optional pieces in separate files,
- Patch the pieces together when you need a runnable configuration.

That can mean swapping parameter sets, comparing systems, changing processing targets, varying backend choices, or adjusting simulation resolution without duplicating large YAML files.

This guide focuses on one of the most common cases: defining a model once and patching in interchangeable parameter groups to build complete configs cheaply.

## 1. Start from the Example Bundle

Download [modular-configuration.zip](../downloads/modular-configuration.zip), unzip it, and enter the project:

```bash
unzip modular-configuration.zip
cd modular-configuration
```

Then create and activate the environment:

```bash
just venv
conda activate ./venv
```

The bundle already includes the wrapper-based SIR model from the quickstart example, a scipy engine plugin, and a set of modular config fragments ready for patching.

## 2. Organize the Model and Parameter Groups Separately

The example project keeps the model definition in one file and splits parameters into reusable groups:

```text
modular-configuration/
├── configs/
│   ├── built/
│   ├── model.yaml
│   └── parameters/
│       ├── initial-state.yaml
│       ├── recovery-standard.yaml
│       ├── transmission-baseline.yaml
│       └── transmission-high.yaml
├── environment.yaml
├── justfile
├── model_input/
│   └── plugins/
│       ├── SIR.py
│       └── solve_ivp.py
└── model_output/
```

The model file contains the system, engine, backend, and simulation target, but no parameters:

??? example "Baseline Model - `configs/model.yaml`"
    ```yaml
    --8<-- "assets/modular-configuration/configs/model.yaml"
    ```

Each parameter-group file contributes just one part of the final `parameters` block:

??? example "Initial Conditions Parameters - `configs/parameters/initial-state.yaml`"
    ```yaml
    --8<-- "assets/modular-configuration/configs/parameters/initial-state.yaml"
    ```

??? example "Transmission Parameters - `configs/parameters/transmission-baseline.yaml`"
    ```yaml
    --8<-- "assets/modular-configuration/configs/parameters/transmission-baseline.yaml"
    ```

??? example "Recovery Parameters - `configs/parameters/recovery-standard.yaml`"
    ```yaml
    --8<-- "assets/modular-configuration/configs/parameters/recovery-standard.yaml"
    ```

This is the core plug-and-play workflow: a complete runnable config is assembled from one model file plus a small set of interchangeable parameter files.

## 3. Patch to Stdout First

By default, `flepimop2 patch` writes the patched configuration to stdout. That is useful when you want to inspect the final YAML before saving it anywhere:

```bash
flepimop2 patch \
  configs/model.yaml \
  configs/parameters/initial-state.yaml \
  configs/parameters/transmission-baseline.yaml \
  configs/parameters/recovery-standard.yaml
```

The output is a complete configuration:

```yaml
name: modular-sir
axes: {}
engines:
  default:
    module: wrapper
    options: null
    state_change: flow
    script: model_input/plugins/solve_ivp.py
systems:
  default:
    module: wrapper
    options: null
    state_change: flow
    script: model_input/plugins/SIR.py
    model_state:
      parameter_names:
      - s0
      - i0
      - r0
      labels:
      - S
      - I
      - R
backends:
  default:
    module: csv
    options: null
    root: model_output
process: {}
parameters:
  s0: fixed(999)
  i0: fixed(1)
  r0: fixed(0)
  beta: fixed(0.3)
  gamma: fixed(0.1)
scenarios: {}
simulate:
  demo:
    engine: default
    system: default
    backend: default
    times: 0.0:1.0:60.0
    params: {}
    scenario: null
```

This is often the fastest way to verify that the pieces you selected produce the config you expect.

## 4. Let `error` Mode Catch Accidental Overlap

The default patch mode is `error`. That is a good default because it catches accidental collisions early.

For example, these two files both define `beta`:

??? example "Alternative Transmission Parameters - `configs/parameters/transmission-high.yaml`"
    ```yaml
    --8<-- "assets/modular-configuration/configs/parameters/transmission-high.yaml"
    ```

If you patch both transmission files into the same build, `flepimop2 patch` stops instead of silently choosing one:

```bash
flepimop2 patch \
  configs/model.yaml \
  configs/parameters/initial-state.yaml \
  configs/parameters/transmission-baseline.yaml \
  configs/parameters/transmission-high.yaml \
  configs/parameters/recovery-standard.yaml
```

Example error:

```text
Cannot patch configuration under conflict='error'; duplicate section keys: parameters=['beta'].
```

This error highlights the portions of the configuration file the conflict. Other patch modes, like 'replace' or 'merge' will attempt to consolidate conflicting sections.

## 5. Write Built Configs to `configs/built/`

Once you know which fragments you want, write the assembled result to `configs/built/`:

```bash
flepimop2 patch \
  configs/model.yaml \
  configs/parameters/initial-state.yaml \
  configs/parameters/transmission-baseline.yaml \
  configs/parameters/recovery-standard.yaml \
  --output configs/built/baseline.yaml
```

If you intentionally want a later file to override an earlier one, opt into `replace` mode and keep the override last:

```bash
flepimop2 patch \
  --patch-mode replace \
  configs/built/baseline.yaml \
  configs/parameters/transmission-high.yaml \
  --output configs/built/high-transmission.yaml
```

Now you can run the built config directly:

```bash
flepimop2 simulate configs/built/high-transmission.yaml
```

`configs/built/` is the right place for generated configs in a project created from `flepimop2 skeleton`. The directory is already set up to stay out of version control, which is what you usually want. Built configs are cheap to reconstruct, so it is more useful to track the modular source pieces than the generated YAML.

## 6. Automate the Build Step in Your Task Runner

If your workflow depends on built configs, make the config build step an explicit dependency in your task runner.

For example, with the default `justfile`, you might add:

```make
build-baseline:
    flepimop2 patch \
      configs/model.yaml \
      configs/parameters/initial-state.yaml \
      configs/parameters/transmission-baseline.yaml \
      configs/parameters/recovery-standard.yaml \
      --output configs/built/baseline.yaml

simulate-baseline: build-baseline
    flepimop2 simulate configs/built/baseline.yaml

build-high-transmission: build-baseline
    flepimop2 patch \
      --patch-mode replace \
      configs/built/baseline.yaml \
      configs/parameters/transmission-high.yaml \
      --output configs/built/high-transmission.yaml

simulate-high-transmission: build-high-transmission
    flepimop2 simulate configs/built/high-transmission.yaml
```

The same idea applies if you use `make` or another task runner/build system, treat config assembly as a first-class build step and make downstream recipes depend on it.

## 7. Summary

`flepimop2 patch` works best when you treat configurations as modular building blocks instead of monolithic files:

- Keep the stable core in one file,
- Split reusable variations into smaller files,
- `error` mode to catch accidental overlap,
- Use `replace` only when you want an explicit override,
- `configs/built/` for generated runnable configs.

The parameter-group example in this guide is only one application of that pattern. The same approach can support model comparison, alternate processing pipelines, backend swaps, target-specific simulation settings, and other composable workflow choices. In all of those cases, the result is the same: projects stay easier to reason about, easier to version, and cheap to rebuild.

For more usage details please refer to the [`flepimop2 patch` CLI reference](../reference/cli.md#flepimop2-patch).
