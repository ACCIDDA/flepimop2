# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Tests for ParameterABC.requested_parameters and dependency resolution."""

import math
from pathlib import Path

import numpy as np
import pytest

import flepimop2.simulator as sim_module
from flepimop2.axis import AxisCollection, ResolvedShape
from flepimop2.configuration import ConfigurationModel
from flepimop2.parameter.abc import ParameterABC, ParameterRequest, ParameterValue
from flepimop2.parameter.fixed import FixedParameter
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


class _DependentParameter(ParameterABC, module="flepimop2.parameter._dep_test"):
    """Test parameter that declares one named dependency and scales its value."""

    factor: float
    dep_name: str

    def requested_parameters(
        self,
        axes: AxisCollection,  # noqa: ARG002
    ) -> dict[str, ParameterRequest]:
        """Return a single dependency request for dep_name."""
        return {self.dep_name: ParameterRequest(name=self.dep_name)}

    def sample(
        self,
        *,
        axes: AxisCollection | None = None,  # noqa: ARG002
        request: ParameterRequest | None = None,  # noqa: ARG002
        params: dict[str, ParameterValue] | None = None,
    ) -> ParameterValue:
        """Return factor * dep_name's scalar value."""
        base = (params or {})[self.dep_name].item()
        return ParameterValue(
            value=np.array(self.factor * base, dtype=np.float64),
            shape=ResolvedShape(),
        )


class _ShapedDependentParameter(
    ParameterABC, module="flepimop2.parameter._shaped_dep_test"
):
    """Test parameter that requests a shaped dependency and sums it element-wise."""

    dep_name: str
    dep_axes: tuple[str, ...]

    def requested_parameters(
        self,
        axes: AxisCollection,  # noqa: ARG002
    ) -> dict[str, ParameterRequest]:
        """Return a dependency request with an explicit axis shape."""
        return {
            self.dep_name: ParameterRequest(
                name=self.dep_name,
                axes=self.dep_axes,
                broadcast=True,
            )
        }

    def sample(
        self,
        *,
        axes: AxisCollection | None = None,  # noqa: ARG002
        request: ParameterRequest | None = None,  # noqa: ARG002
        params: dict[str, ParameterValue] | None = None,
    ) -> ParameterValue:
        """Return the resolved dependency value unchanged."""
        dep = (params or {})[self.dep_name]
        return ParameterValue(value=dep.value, shape=dep.shape)


def _make_simulator(
    parameter_instances: dict[str, ParameterABC],
    tmp_path: Path,
) -> Simulator:
    """Build a Simulator whose parameter_configs hold pre-built instances.

    The config is validated with fixed=0.0 stubs so pydantic is happy;
    parameter_configs is then replaced with the real instances, and
    build_parameter is patched to return the instance directly.

    Args:
        parameter_instances: Mapping of parameter name to pre-built instance.
        tmp_path: Temporary directory for backend output.

    Returns:
        A configured Simulator ready for resolution tests.
    """
    output_root = tmp_path / "model_output"
    output_root.mkdir()
    stub = {name: {"module": "fixed", "value": 0.0} for name in parameter_instances}
    config = ConfigurationModel.model_validate({
        "systems": {
            "demo": {
                "module": "wrapper",
                "script": SYSTEM_SCRIPT,
                "state_change": "flow",
                "requested_parameters": {"beta": None, "gamma": None},
                "model_state": {"parameter_names": ["s0", "i0", "r0"]},
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
        "parameters": stub,
        "simulate": {
            "demo": {
                "system": "demo",
                "engine": "demo",
                "backend": "demo",
                "times": [0.0, 1.0],
            }
        },
    })
    sim = Simulator.from_configuration_model(config)
    sim.parameter_configs = parameter_instances  # type: ignore[assignment]
    return sim


def test_requested_parameters_default_returns_empty_dict() -> None:
    """ParameterABC.requested_parameters returns {} by default."""
    assert FixedParameter(value=1.0).requested_parameters(AxisCollection()) == {}


def test_fixed_parameter_sample_accepts_params_kwarg() -> None:
    """FixedParameter.sample accepts the params kwarg without error."""
    dep = ParameterValue(value=np.array(99.0), shape=ResolvedShape())
    result = FixedParameter(value=math.pi).sample(params={"unused": dep})
    assert result.item() == pytest.approx(math.pi)


def test_fixed_parameter_sample_params_none_is_default() -> None:
    """Passing params=None is equivalent to omitting the argument."""
    r1 = FixedParameter(value=1.0).sample()
    r2 = FixedParameter(value=1.0).sample(params=None)
    assert r1.item() == r2.item()


def test_simulator_dependency_resolution_passes_params_to_sample(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_sample_parameter resolves a dependency and passes its value via params."""
    base_param = FixedParameter(value=5.0)
    dep_param = _DependentParameter(factor=2.0, dep_name="base")
    instances: dict[str, ParameterABC] = {
        "s0": FixedParameter(value=1.0),
        "i0": FixedParameter(value=0.0),
        "r0": FixedParameter(value=0.0),
        "base": base_param,
        "dep": dep_param,
        "gamma": FixedParameter(value=0.1),
    }

    output_root = tmp_path / "model_output"
    output_root.mkdir()
    config = ConfigurationModel.model_validate({
        "systems": {
            "demo": {
                "module": "wrapper",
                "script": SYSTEM_SCRIPT,
                "state_change": "flow",
                "requested_parameters": {"dep": None, "gamma": None},
                "model_state": {"parameter_names": ["s0", "i0", "r0"]},
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
        "parameters": {name: {"module": "fixed", "value": 0.0} for name in instances},
        "simulate": {
            "demo": {
                "system": "demo",
                "engine": "demo",
                "backend": "demo",
                "times": [0.0, 1.0],
            }
        },
    })
    sim = Simulator.from_configuration_model(config)
    sim.parameter_configs = instances  # type: ignore[assignment]
    real_build = sim_module.build_parameter  # type: ignore[attr-defined]
    monkeypatch.setattr(
        sim_module,
        "build_parameter",
        lambda cfg: cfg if isinstance(cfg, ParameterABC) else real_build(cfg),
    )

    _, params = sim.resolve_inputs()
    assert params["dep"].item() == pytest.approx(10.0)


def test_simulator_detects_direct_circular_dependency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_sample_parameter raises ValueError when a parameter requests itself."""
    self_dep = _DependentParameter(factor=1.0, dep_name="beta")
    instances: dict[str, ParameterABC] = {
        "s0": FixedParameter(value=1.0),
        "i0": FixedParameter(value=0.0),
        "r0": FixedParameter(value=0.0),
        "beta": self_dep,
        "gamma": FixedParameter(value=0.1),
    }
    sim = _make_simulator(instances, tmp_path)
    real_build = sim_module.build_parameter  # type: ignore[attr-defined]
    monkeypatch.setattr(
        sim_module,
        "build_parameter",
        lambda cfg: cfg if isinstance(cfg, ParameterABC) else real_build(cfg),
    )

    with pytest.raises(ValueError, match="Circular parameter dependency detected"):
        sim.resolve_inputs()


def test_requested_parameters_with_explicit_axis_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dependency requested with an axis shape is resolved to that shape.

    _ShapedDependentParameter requests its dependency with axes=("age",) and
    broadcast=True, so a scalar FixedParameter dependency should be broadcast
    to the size of the age axis before being passed to sample.
    """
    axes_config = {"age": {"kind": "categorical", "labels": ["0-17", "18-64", "65+"]}}
    shaped_dep = _ShapedDependentParameter(dep_name="base", dep_axes=("age",))
    instances: dict[str, ParameterABC] = {
        "s0": FixedParameter(value=1.0),
        "i0": FixedParameter(value=0.0),
        "r0": FixedParameter(value=0.0),
        "base": FixedParameter(value=0.5),
        "beta": shaped_dep,
        "gamma": FixedParameter(value=0.1),
    }

    output_root = tmp_path / "model_output"
    output_root.mkdir()
    config = ConfigurationModel.model_validate({
        "axes": axes_config,
        "systems": {
            "demo": {
                "module": "wrapper",
                "script": SYSTEM_SCRIPT,
                "state_change": "flow",
                "requested_parameters": {"beta": None, "gamma": None},
                "model_state": {"parameter_names": ["s0", "i0", "r0"]},
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
        "parameters": {name: {"module": "fixed", "value": 0.0} for name in instances},
        "simulate": {
            "demo": {
                "system": "demo",
                "engine": "demo",
                "backend": "demo",
                "times": [0.0, 1.0],
            }
        },
    })
    sim = Simulator.from_configuration_model(config)
    sim.parameter_configs = instances  # type: ignore[assignment]
    real_build = sim_module.build_parameter  # type: ignore[attr-defined]
    monkeypatch.setattr(
        sim_module,
        "build_parameter",
        lambda cfg: cfg if isinstance(cfg, ParameterABC) else real_build(cfg),
    )

    _, params = sim.resolve_inputs()

    assert params["beta"].shape.axis_names == ("age",)
    assert params["beta"].shape.sizes == (3,)
    np.testing.assert_array_equal(params["beta"].value, np.array([0.5, 0.5, 0.5]))


def test_requested_parameter_missing_from_configuration_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_sample_parameter raises KeyError when a declared dependency is not configured.

    If a parameter's requested_parameters declares a name that has no entry
    in the configuration, the Simulator raises KeyError with a clear message
    before any sampling takes place.
    """
    dep_param = _DependentParameter(factor=2.0, dep_name="missing_dep")
    instances: dict[str, ParameterABC] = {
        "s0": FixedParameter(value=1.0),
        "i0": FixedParameter(value=0.0),
        "r0": FixedParameter(value=0.0),
        "beta": dep_param,
        "gamma": FixedParameter(value=0.1),
    }
    sim = _make_simulator(instances, tmp_path)
    real_build = sim_module.build_parameter  # type: ignore[attr-defined]
    monkeypatch.setattr(
        sim_module,
        "build_parameter",
        lambda cfg: cfg if isinstance(cfg, ParameterABC) else real_build(cfg),
    )

    with pytest.raises(KeyError, match="missing_dep"):
        sim.resolve_inputs()


def test_simulator_detects_indirect_circular_dependency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_sample_parameter raises ValueError for A -> B -> A cycles."""
    beta_param = _DependentParameter(factor=1.0, dep_name="gamma_dep")
    gamma_dep = _DependentParameter(factor=1.0, dep_name="beta")
    instances: dict[str, ParameterABC] = {
        "s0": FixedParameter(value=1.0),
        "i0": FixedParameter(value=0.0),
        "r0": FixedParameter(value=0.0),
        "beta": beta_param,
        "gamma_dep": gamma_dep,
        "gamma": FixedParameter(value=0.1),
    }
    sim = _make_simulator(instances, tmp_path)
    real_build = sim_module.build_parameter  # type: ignore[attr-defined]
    monkeypatch.setattr(
        sim_module,
        "build_parameter",
        lambda cfg: cfg if isinstance(cfg, ParameterABC) else real_build(cfg),
    )

    with pytest.raises(ValueError, match="Circular parameter dependency detected"):
        sim.resolve_inputs()
