# Integration Testing

This tutorial will show how to:

- Use `flepimop2.testing` helpers to run end-to-end scenarios.
- Validate real CLI behavior in a project context or an external provider package context.

## Why do Integration Test?

Integration tests are for checking that packages behave as a user would expect when used with the `flepimop2` CLI and infrastructure. They are slower than unit tests because they create projects, invoke commands, and run simulations. That cost is worth it when you want confidence that all the pieces work together.

Because they are slower, integration tests should be broad. Prefer a single test that exercises a full workflow with several assertions rather than lots of tiny variants. Use unit tests for edge cases and fast iteration, and use integration tests for end-to-end scenarios.

## Integration Testing in a Project Context

The most common type of integration testing, especially for developers of external package providers, is running the `flepimop2` CLI in a project context. The primary functions a user will use are `project_skeleton`, which will setup a project in the given directory, and `flepimop2_run`, which will run the `flepimop2` CLI in the context of that project.

```python title="tests/integration/my_integration_test/test_simulate.py"
from pathlib import Path

from flepimop2.testing import flepimop2_run, project_skeleton

def test_simulate(tmp_path: Path) -> None:
    project_skeleton(
        tmp_path,
        copy_files={
            Path("tests/integration/my_integration_test/sir.py"): Path(
                "model_input/plugins/sir.py"
            ),
            Path("tests/integration/my_integration_test/solve_ivp.py"): Path(
                "model_input/plugins/solve_ivp.py"
            ),
            Path("tests/integration/my_integration_test/config.yaml"): Path(
                "configs/config.yaml"
            ),
        },
        dependencies=["numpy", "pandas", "scipy"],
    )
    result = flepimop2_run(
        "simulate",
        args=["configs/config.yaml"],
        cwd=tmp_path,
    )
    assert result.returncode == 0
```

Above is a brief example of what an integration test might look like. The key elements of this example are:

- The test provides a temporary directory to `project_skeleton` and `flepimop2_run` that is cleaned up after test completion via [`pytest`'s `tmp_path` fixture](https://docs.pytest.org/en/stable/how-to/tmp_path.html).
- The files `sir.py`, `solve_ivp.py`, and `config.yaml` are copied from the integration test to the project directory after the project is created via the `flepimop2 skeleton` CLI.
- The dependencies `numpy`, `pandas`, and `scipy` are additionally installed to the project directory's virtual environment and are available to the `flepimop2` CLI.
- Finally, the `flepimop2_run` function invokes the `flepimop2 simulate` CLI in the project directory and the returned object is a [`subprocess.CompletedProcess`](https://docs.python.org/3/library/subprocess.html#subprocess.CompletedProcess). However, you could invoke any action available via the `flepimop2` CLI, for a full list please refer to `flepimop2 --help`.

From here a developer would be able to make further assertions about the output of the CLI command itself or contents of the project directory to ensure that the integration test has worked as expected.

## Integration Testing in an External Provider Package Context

For tests that need to simulate an external provider package, use `external_provider_package`. This helper constructs an implicit namespace package under `flepimop2.*`, installs it into a temporary virtual environment, and lets you run the CLI against it using `flepimop2_run`. This kind of integration test is very uncommon outside of development for `flepimop2` itself since this is largely about testing the ability for the `flepimop2` package to interact with external package providers.

```python title="tests/integration/external_provider/test_simulate.py"
from pathlib import Path

from flepimop2.testing import external_provider_package, flepimop2_run

def test_simulate(tmp_path: Path) -> None:
    external_provider_package(
        tmp_path,
        copy_files={
            Path("tests/integration/external_provider/euler.py"): Path(
                "external_provider/src/flepimop2/engine/euler.py"
            ),
            Path("tests/integration/external_provider/sir.py"): Path(
                "external_provider/src/flepimop2/system/sir.py"
            ),
            Path("tests/integration/external_provider/config.yaml"): Path(
                "config.yaml"
            ),
        },
        dependencies=["numpy", "scipy"],
    )
    result = flepimop2_run(
        "simulate",
        args=["config.yaml"],
        cwd=tmp_path,
    )
    assert result.returncode == 0
```

Above is a brief example of what an integration test might look like. Similar to the previous example, the key elements of this example are the same, except the `external_provider_package` creates an external provider package named "example-provider".

## Summary

Integration tests validate the end-to-end user experience of `flepimop2` using real projects and real CLI commands. Use `project_skeleton` for project workflows, and use `external_provider_package` when you need to simulate a provider package install.

For API details please refer to the [`flepimop2.testing` API reference](./../reference/api/testing.md) and for working examples you can refer to the [`flepimop2` integration tests](https://github.com/ACCIDDA/flepimop2/tree/main/tests/integration).
