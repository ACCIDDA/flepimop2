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
    ```python
    --8<-- "assets/plot_scenarios.R"
    ```

