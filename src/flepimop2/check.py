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
"""Whole-configuration validation that reports issues instead of raising.

`check_configuration` walks a configuration the way `simulate` and
`process` would, but stops short of running anything. Every problem found is
returned as a `ValidationIssue` so a user sees all of them at once:

- the configuration file parses and validates;
- each simulate target builds its system, engine, and backend;
- every parameter the system requests is configured (unless optional) and
  samples to the shape it was requested with;
- each process step builds and passes its `_process_validate` hook.

This is the minimal `flepimop2 check` from issue #25. Components add richer
checks by extending their existing validation hooks.
"""

__all__ = ["check_configuration"]

from pathlib import Path

from flepimop2.configuration import ConfigurationModel
from flepimop2.exceptions import ValidationIssue
from flepimop2.process.abc import build as build_process
from flepimop2.simulator import Simulator


def _issue(kind: str, exc: BaseException, **ctx: object) -> ValidationIssue:
    message = str(exc) or type(exc).__name__
    return ValidationIssue(
        msg=message, kind=kind, ctx={**ctx, "error": type(exc).__name__}
    )


def _check_simulate_target(
    config: ConfigurationModel, target: str | None
) -> list[ValidationIssue]:
    label = target or "<default>"
    try:
        simulator = Simulator.from_configuration_model(config, target=target)
    except Exception as exc:  # noqa: BLE001 - report, do not raise
        return [_issue("simulator_build", exc, target=label)]

    issues: list[ValidationIssue] = []
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

    configured = simulator.parameter_configs or {}
    for name, request in requests.items():
        if name not in configured:
            if not request.optional:
                issues.append(
                    ValidationIssue(
                        msg=(
                            f"Required parameter '{name}' was requested "
                            "but not configured."
                        ),
                        kind="missing_parameter",
                        ctx={"target": label, "parameter": name},
                    )
                )
            continue
        try:
            value = simulator._sample_parameter(name, request)  # noqa: SLF001
        except Exception as exc:  # noqa: BLE001
            issues.append(
                _issue("parameter_resolution", exc, target=label, parameter=name)
            )
            continue
        if request.axes and not request.broadcast:
            expected = simulator.axes.resolve_shape(tuple(request.axes)).sizes
            actual = tuple(value.shape.sizes)
            if actual != tuple(expected):
                issues.append(
                    ValidationIssue(
                        msg=(
                            f"Parameter '{name}' has shape {actual}; "
                            f"requested {tuple(expected)} over {tuple(request.axes)}."
                        ),
                        kind="parameter_shape",
                        ctx={"target": label, "parameter": name},
                    )
                )
    return issues


def check_configuration(
    config: ConfigurationModel | Path | str,
) -> list[ValidationIssue]:
    """Return every validation issue found in a configuration.

    Args:
        config: A configuration model or a path to a configuration file.

    Returns:
        The validation issues found; an empty list means the configuration
        passed every check.
    """
    if isinstance(config, ConfigurationModel):
        model = config
    else:
        try:
            model = ConfigurationModel.from_yaml(Path(config))
        except Exception as exc:  # noqa: BLE001
            return [_issue("configuration", exc, path=str(config))]

    issues: list[ValidationIssue] = []
    targets: list[str | None] = list(model.simulate) if model.simulate else []
    for target in targets:
        issues.extend(_check_simulate_target(model, target))

    for name, process_config in model.process.items():
        try:
            process = build_process(process_config)
        except Exception as exc:  # noqa: BLE001
            issues.append(_issue("process_build", exc, process=name))
            continue
        try:
            result = process._process_validate()  # noqa: SLF001
        except Exception as exc:  # noqa: BLE001
            issues.append(_issue("process_validation", exc, process=name))
            continue
        issues.extend(
            ValidationIssue(
                msg=issue.msg,
                kind=issue.kind,
                ctx={**(issue.ctx or {}), "process": name},
            )
            for issue in result or []
        )
    return issues
