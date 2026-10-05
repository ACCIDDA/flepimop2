# Generating Scenario Results

Building on the quick start material, let's take on the common task of needing to simulate for several different parameter scenarios. We can do this by adding a `scenarios` block to pipeline configuration.

??? example "Configuration File - `configs/scenarios_config.yaml`"
    ```yaml hl_lines="35-39"
    --8<-- "assets/scenarios_config.yaml"
    ```

```bash
flepimop2 simulate scenarios_config.yaml # run the scenarios
ls model_output # should show 9 entries
flepimop2 process scenarios_config.yaml
```

The processing step uses the outputs to create a plot.

??? example "Processing Script - `model_input/plot_scenarios.R`"
    ```r
    --8<-- "assets/plot_scenarios.R"
    ```

## Running a processing step per scenario

Above, one processing step consumes the outputs of every scenario at once. The
other common shape is the opposite: run the *same* processing step once per
scenario, with each run given that scenario's values. List the process step
under the scenario that should run it:

```yaml
scenarios:
  sweep:
    module: grid
    processes: [analyze]
    parameters:
      beta: [0.1, 0.2]
      gamma: [0.05]

process:
  fetch:
    module: shell
    command: ./fetch_inputs.sh
  analyze:
    module: shell
    depends: [fetch]
    command: Rscript
    args: ["analyze.R", "--beta", "{beta}", "--gamma", "{gamma}",
           "--output", "plots/beta-{beta}-gamma-{gamma}.png"]
```

`flepimop2 process -t analyze` runs `fetch` once and then `analyze` twice, once
for `beta=0.1` and once for `beta=0.2`. A `grid` scenario takes the Cartesian
product of its parameters, so adding a second value for `gamma` above would give
four runs rather than two. An ordinary step such as `fetch` runs once. Multiple
scenarios may list `analyze`; its runs then follow the order of those scenarios
in the configuration. Unrelated scenarios do not cause extra runs.

Scenario values are filled in wherever the step's configuration mentions them as
`{name}`, in any string field, including inside lists. Only the names the
scenario actually defines are substituted, so other braces are left alone and a
command such as `awk '{print $1}'` keeps working. The `module` and `depends`
keys describe the step itself and are never rewritten. Scenario values are
inserted as text in one pass, so a value that contains `{other}` is not
interpreted again.

Give each run a distinct output target when the process writes files, as the
`--output` argument does above. A process module decides when its own output is
already satisfied; the core runner does not assign output paths or cache keys.

A parameterized step stays a single node in the dependency graph. Anything that
declares `depends: [analyze]` therefore runs after *all* of `analyze`'s
scenarios have finished, rather than once per scenario.
