# From a First Simulation to Research Workflows

The [quickstart](../index.md) gets a small SIR model running and creates a plot. From there, stay in the flepimop2 documentation to explore model assumptions and compare scenarios. Parameter inference is also possible in projects that provide an inference plugin; the implementation and commands depend on that project.

## 1. Run and understand a baseline

Follow the [quickstart](../index.md) to install flepimop2, create the bundled project, and run its SIR simulation:

```bash
flepimop2 simulate configs/config.yaml
flepimop2 process configs/config.yaml
```

The simulation writes results under `model_output/`, and the processing step uses the configured script to create a plot. This gives you a baseline to compare with later runs.

## 2. Explore how assumptions change outcomes

For a first experiment, change one model parameter in `configs/config.yaml`, rerun the simulation and processing steps, and compare the result with your baseline. For example, the quickstart SIR configuration has `beta` and `gamma` parameters.

**Concrete quickstart experiment:** In the project created by the quickstart, first preserve the baseline plot. Then change `beta` from `0.3` to `0.6` in `configs/config.yaml`, leaving `gamma` and the initial state unchanged. From the project directory, run:

```bash
cp model_output/SIR_plot.png model_output/SIR_plot_baseline.png
flepimop2 simulate configs/config.yaml
flepimop2 process configs/config.yaml
```

Compare `model_output/SIR_plot.png` with `model_output/SIR_plot_baseline.png`. With this SIR model, the larger transmission rate should make infections rise faster. If post-processing reports a missing R package on macOS, see the [quickstart's R troubleshooting note](../index.md#adding-post-processing).

Next, try a set of parameter values in one run using a scenario configuration. The [scenario results guide](scenarios.md) introduces the `scenarios` block, and the [vaccination campaign scenario-grid example](vaccination-campaign-scenario-grid-example.md) demonstrates a larger policy sweep with plots and summary measures.

A scenario sweep runs forward simulations for values you select. It helps answer questions such as “How do outcomes change if this parameter or intervention differs?” It does not estimate unknown parameters from observations.

## 3. Understand where parameter inference fits

Parameter inference uses observed data to estimate unknown parameters and quantify uncertainty. flepimop2 does not expose a single built-in `flepimop2 infer` command for every model. An inference workflow is provided by the project, typically as a plugin invoked through a named `process` target in that project's configuration.

When you use a project with inference, look in its documentation and configuration for the observed-data inputs, inference target, and posterior-predictive targets. The project documentation should explain how to run the fit and find its outputs. Inference is an optional, project-specific extension to the beginner workflow.

### What an inference workflow usually involves

The exact methods and commands depend on the project, but an inference workflow commonly follows these stages:

1. Prepare observed data and specify how the data correspond to model outputs.
2. Check whether the chosen parameter ranges produce plausible model behavior, often with prior-predictive simulations.
3. Fit the model to the observations using the project's inference method.
4. Inspect the fit and compare posterior-predictive simulations with the observed data.
5. Use fitted parameter values or samples for projections and scenario analysis, while carrying forward relevant uncertainty.

These steps are not built-in `flepimop2` commands. Follow the project documentation for its data format, targets, inference method, diagnostics, and outputs.

## Keep runs reproducible

Keep the configuration, data or data references, and scripts needed to explain how a result was produced. Record which simulation or process target you ran and keep generated outputs separate from source inputs unless the project asks you to version a specific derived artifact.

For more on model and solver configuration, see the [getting-started guide](getting-started.md). For parameter sweeps, start with [Generating Scenario Results](scenarios.md).
