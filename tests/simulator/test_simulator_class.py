"""Tests for simulator input resolution from system contracts."""

from pathlib import Path

import numpy as np
import pytest

from flepimop2.configuration import ConfigurationModel
from flepimop2.simulator import Simulator

ENGINE_SCRIPT = (
    Path(__file__).parent.parent
    / "engine"
    / "engine_wrapper_assets"
    / "dummy_engine.py"
)
SYSTEM_SCRIPT = (
    Path(__file__).parent.parent
    / "system"
    / "system_wrapper_assets"
    / "wrapper_system_with_extras.py"
)


def test_simulator_resolves_inputs_and_runs(
    tmp_path: Path,
) -> None:
    """Simulator should resolve structured inputs and execute the engine."""
    output_root = tmp_path / "model_output"
    output_root.mkdir()
    config = ConfigurationModel.model_validate({
        "axes": {
            "age": {
                "kind": "categorical",
                "labels": ["0-17", "18-64", "65+"],
            }
        },
        "systems": {
            "demo": {
                "module": "wrapper",
                "script": SYSTEM_SCRIPT,
                "state_change": "flow",
            }
        },
        "engines": {
            "demo": {
                "module": "wrapper",
                "script": ENGINE_SCRIPT,
                "state_change": "flow",
            }
        },
        "backends": {"demo": {"module": "csv", "root": output_root}},
        "parameters": {
            "s0": {"module": "fixed", "value": 100.0},
            "i0": {"module": "fixed", "value": 1.0},
            "r0": {"module": "fixed", "value": 0.0},
            "beta": {"module": "fixed", "value": 0.3},
            "gamma": {"module": "fixed", "value": 0.1},
        },
        "simulate": {
            "demo": {
                "system": "demo",
                "engine": "demo",
                "backend": "demo",
                "times": [0.0, 1.0],
            }
        },
    })

    simulator = Simulator.from_configuration_model(config)
    initial_state, params = simulator.resolve_inputs()

    assert tuple(initial_state) == ("s0", "i0", "r0")
    np.testing.assert_array_equal(initial_state["s0"].value, np.array([100.0] * 3))
    np.testing.assert_array_equal(initial_state["i0"].value, np.array([1.0] * 3))
    np.testing.assert_array_equal(initial_state["r0"].value, np.array([0.0] * 3))
    assert params["beta"].item() == pytest.approx(0.3)
    np.testing.assert_array_equal(params["gamma"].value, np.array([0.1, 0.1, 0.1]))

    result = simulator.run(initial_state, params)

    assert result.shape == (2, 10)
    np.testing.assert_array_equal(result[:, 0], np.array([0.0, 1.0]))
    np.testing.assert_array_equal(
        result[0, 1:],
        np.array([100.0, 100.0, 100.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0]),
    )
    np.testing.assert_allclose(
        result[1, 1:],
        np.array([100.4, 100.4, 100.4, 1.4, 1.4, 1.4, 0.4, 0.4, 0.4]),
    )
