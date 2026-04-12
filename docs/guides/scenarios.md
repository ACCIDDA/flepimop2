# Generating Scenario Results

Building on the quick start material, let's take on the common task of needing to simulate for several different parameter scenarios. We can do this by adding a `scenarios` block to pipeline configuration.

??? example "Configuration File - `configs/scenarios_config.yaml`"
    ```yaml hl_lines="35-39"
    --8<-- "assets/scenarios_config.yaml"
    ```

```bash
flepimop2 simulate scenarios_config.yaml
```