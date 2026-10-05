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
"""Whole-configuration validation that reports issues instead of raising.

`check_configuration` walks a configuration hierarchically through four
distinct validation stages, stopping short of executing any simulation or
process commands:

1. **Intra-Module Validation**:
   - Parses and validates the file as a `ConfigurationModel`;
   - Validates declared `axes` definitions;
   - Builds each configured component instance across all top-level module
     sections (`engines`, `systems`, `backends`, `parameters`, `process`,
     `jobs`, `scenarios`) and runs its `validate_module()` hook.

2. **Referential Integrity Validation**:
   - Verifies that cross-referenced target identifiers (e.g. `simulate` target
     references to systems, engines, backends, and scenarios; `process`
     dependencies) exist in their respective configuration sections.

3. **Acyclic / DAG Integrity Validation**:
   - Validates that inter-module dependencies (such as process step DAGs) form
     a directed acyclic graph with no self-dependencies or cycles.

4. **Contract & Compatibility Validation**:
   - Verifies that referenced components satisfy inter-module contracts:
     checks `engine.validate_system(system)` compatibility, verifies that
     required system parameters are configured, and verifies that parameter
     shapes match the requested axes dimensions.

All problems are accumulated and returned as `ValidationIssue`s so a user sees
every issue across the entire configuration at once.
"""

__all__ = ["check_configuration"]

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Final

from flepimop2.axis import AxisCollection
from flepimop2.backend.abc import build as build_backend
from flepimop2.configuration import ConfigurationModel
from flepimop2.engine.abc import build as build_engine
from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue
from flepimop2.job.abc import build as build_job
from flepimop2.module import ModuleBase
from flepimop2.parameter.abc import build as build_parameter
from flepimop2.process.abc import build as build_process
from flepimop2.process.abc import resolve_plan
from flepimop2.scenario.abc import build as build_scenario
from flepimop2.simulator import Simulator
from flepimop2.system.abc import build as build_system

_SECTION_BUILDERS: Final[dict[str, tuple[str, Callable[[Any], ModuleBase]]]] = {
    "engines": ("engine", build_engine),
    "systems": ("system", build_system),
    "backends": ("backend", build_backend),
    "parameters": ("parameter", build_parameter),
    "process": ("process", build_process),
    "jobs": ("job", build_job),
    "scenarios": ("scenario", build_scenario),
}


def _issue(kind: str, exc: BaseException, **ctx: object) -> ValidationIssue:
    message = str(exc) or type(exc).__name__
    return ValidationIssue(
        msg=message, kind=kind, ctx={**ctx, "error": type(exc).__name__}
    )


def _check_top_level_sections(model: ConfigurationModel) -> list[ValidationIssue]:
    """Validate individual module instances across all top-level sections.

    Args:
        model: The configuration model to check.

    Returns:
        A list of validation issues found in top-level sections.
    """
    issues: list[ValidationIssue] = []

    if model.axes:
        try:
            AxisCollection.from_config(model.axes)
        except Exception as exc:  # noqa: BLE001
            issues.append(_issue("axis_validation", exc, section="axes"))

    for section_name, (singular, builder) in _SECTION_BUILDERS.items():
        section_data = getattr(model, section_name, {})
        if not section_data or not isinstance(section_data, Mapping):
            continue
        for target_name, target_config in section_data.items():
            ctx = {
                "section": section_name,
                "target": str(target_name),
                singular: str(target_name),
            }
            try:
                instance = builder(target_config)
            except Exception as exc:  # noqa: BLE001
                issues.append(_issue(f"{singular}_build", exc, **ctx))
                continue
            try:
                module_issues = instance.validate_module()
            except Exception as exc:  # noqa: BLE001
                issues.append(_issue(f"{singular}_validation", exc, **ctx))
                continue
            for issue in module_issues or []:
                merged_ctx = {**ctx, **(issue.ctx or {})}
                issues.append(
                    ValidationIssue(
                        msg=issue.msg,
                        kind=issue.kind,
                        ctx=merged_ctx,
                    )
                )

    return issues


def _check_referential_integrity(
    model: ConfigurationModel,
) -> list[ValidationIssue]:
    """Validate that all referenced components exist in the configuration.

    Args:
        model: The configuration model to check.

    Returns:
        A list of missing dependency validation issues.
    """
    issues: list[ValidationIssue] = []

    for name, spec in model.simulate.items():
        if spec.system not in model.systems:
            issues.append(
                ValidationIssue(
                    msg=(
                        f"Simulate target '{name}' references unknown system "
                        f"'{spec.system}'."
                    ),
                    kind="missing_dependency",
                    ctx={
                        "target": str(name),
                        "section": "systems",
                        "dependency": str(spec.system),
                    },
                )
            )
        if spec.engine not in model.engines:
            issues.append(
                ValidationIssue(
                    msg=(
                        f"Simulate target '{name}' references unknown engine "
                        f"'{spec.engine}'."
                    ),
                    kind="missing_dependency",
                    ctx={
                        "target": str(name),
                        "section": "engines",
                        "dependency": str(spec.engine),
                    },
                )
            )
        if spec.backend not in model.backends:
            issues.append(
                ValidationIssue(
                    msg=(
                        f"Simulate target '{name}' references unknown backend "
                        f"'{spec.backend}'."
                    ),
                    kind="missing_dependency",
                    ctx={
                        "target": str(name),
                        "section": "backends",
                        "dependency": str(spec.backend),
                    },
                )
            )
        if spec.scenario is not None and spec.scenario not in model.scenarios:
            issues.append(
                ValidationIssue(
                    msg=(
                        f"Simulate target '{name}' references unknown scenario "
                        f"'{spec.scenario}'."
                    ),
                    kind="missing_dependency",
                    ctx={
                        "target": str(name),
                        "section": "scenarios",
                        "dependency": str(spec.scenario),
                    },
                )
            )

    return issues


def _check_acyclic_dependencies(
    model: ConfigurationModel,
) -> list[ValidationIssue]:
    """Validate that dependency graphs (e.g. process DAGs) are acyclic.

    Args:
        model: The configuration model to check.

    Returns:
        A list of dependency cycle or unknown dependency issues.
    """
    if not model.process:
        return []
    try:
        resolve_plan(model.process)
    except Flepimop2ValidationError as exc:
        return list(exc.issues)
    except Exception as exc:  # noqa: BLE001
        return [_issue("dependency_cycle", exc, section="process")]
    return []


def _check_parameter_request(
    simulator: Simulator,
    label: str,
    name: str,
    request: Any,  # noqa: ANN401
) -> list[ValidationIssue]:
    """Validate a single parameter request against configured parameter shapes.

    Args:
        simulator: The configured simulator instance.
        label: The label for the simulate target.
        name: The name of the parameter.
        request: The parameter request specification.

    Returns:
        A list of parameter validation issues.
    """
    configured = simulator.parameter_configs or {}
    if name not in configured:
        if not request.optional:
            return [
                ValidationIssue(
                    msg=(
                        f"Required parameter '{name}' was requested but not configured."
                    ),
                    kind="missing_parameter",
                    ctx={"target": label, "parameter": name},
                )
            ]
        return []

    try:
        value = simulator._sample_parameter(name, request)  # noqa: SLF001
    except Exception as exc:  # noqa: BLE001
        return [_issue("parameter_resolution", exc, target=label, parameter=name)]

    if request.axes and not request.broadcast:
        expected = simulator.axes.resolve_shape(tuple(request.axes)).sizes
        actual = tuple(value.shape.sizes)
        if actual != tuple(expected):
            return [
                ValidationIssue(
                    msg=(
                        f"Parameter '{name}' has shape {actual}; "
                        f"requested {tuple(expected)} over {tuple(request.axes)}."
                    ),
                    kind="parameter_shape",
                    ctx={"target": label, "parameter": name},
                )
            ]
    return []


def _check_contract_compatibility(
    model: ConfigurationModel,
) -> list[ValidationIssue]:
    """Validate inter-module contracts (engine-system, parameter-axes).

    Args:
        model: The configuration model to check.

    Returns:
        A list of contract compatibility issues.
    """
    issues: list[ValidationIssue] = []

    for target in model.simulate:
        label = str(target)
        try:
            simulator = Simulator.from_configuration_model(model, target=target)
        except Flepimop2ValidationError as exc:
            issues.extend(exc.issues)
            continue
        except Exception as exc:  # noqa: BLE001
            issues.append(_issue("simulator_build", exc, target=label))
            continue

        try:
            if (
                engine_issues := simulator.engine.validate_system(simulator.system)
            ) is not None:
                issues.extend(engine_issues)
        except Exception as exc:  # noqa: BLE001
            issues.append(_issue("engine_system_validation", exc, target=label))

        try:
            state_spec = simulator.system.model_state(simulator.axes)
        except Exception as exc:  # noqa: BLE001
            issues.append(_issue("model_state", exc, target=label))
            state_spec = None
        requests = dict(state_spec.requests()) if state_spec is not None else {}
        try:
            requests.update(simulator.system.requested_parameters(simulator.axes))
        except Exception as exc:  # noqa: BLE001
            issues.append(_issue("requested_parameters", exc, target=label))

        for name, request in requests.items():
            issues.extend(_check_parameter_request(simulator, label, name, request))

    return issues


def check_configuration(
    config: ConfigurationModel | Path | str | Mapping[str, Any],
) -> list[ValidationIssue]:
    """Return every validation issue found in a configuration.

    Args:
        config: A configuration model, path to a configuration file, or
            raw configuration dictionary.

    Returns:
        The validation issues found; an empty list means the configuration
        passed every check.
    """
    if isinstance(config, ConfigurationModel):
        model = config
    elif isinstance(config, Path | str):
        try:
            model = ConfigurationModel.from_yaml(Path(config))
        except Exception as exc:  # noqa: BLE001
            return [_issue("configuration", exc, path=str(config))]
    elif isinstance(config, Mapping):
        try:
            model = ConfigurationModel.model_validate(config)
        except Exception as exc:  # noqa: BLE001
            return [_issue("configuration", exc)]
    else:
        return [
            ValidationIssue(
                msg=f"Unsupported configuration input type: {type(config).__name__}",
                kind="configuration",
            )
        ]

    issues: list[ValidationIssue] = []

    # 1. Intra-module self-validation across all top-level sections
    issues.extend(_check_top_level_sections(model))

    # 2. Referential integrity across declared dependencies
    issues.extend(_check_referential_integrity(model))

    # 3. Acyclic / DAG dependency validation
    issues.extend(_check_acyclic_dependencies(model))

    # 4. Inter-module contract & compatibility validation
    issues.extend(_check_contract_compatibility(model))

    return issues
