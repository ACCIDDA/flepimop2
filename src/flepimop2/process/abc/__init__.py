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
"""Abstract base class for flepimop2 processing steps."""

__all__ = [
    "ProcessABC",
    "build",
    "expand_scenarios",
    "resolve_plan",
    "validate_scenarios",
]

import re
from abc import abstractmethod
from collections.abc import Mapping
from typing import Any

from pydantic import Field

from flepimop2._utils._module import _as_dict, _build
from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue
from flepimop2.module import ModuleBase
from flepimop2.scenario.abc import build as build_scenario

# Configuration keys that describe the step itself rather than its work, and so
# are never rewritten by a scenario.
_STRUCTURAL_KEYS = frozenset({"module", "depends", "scenario"})
_PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")


class ProcessABC(ModuleBase, module_namespace="process"):
    """
    Abstract base class for flepimop2 processing steps.

    Attributes:
        depends: Names of process steps in the same configuration section that
            must run before this one. These are opaque identifiers, i.e. sibling
            keys of the `process:` section, not filesystem paths: core orders
            steps but does not know what any of them produces.
        scenario: Optional name of an entry in the top-level `scenarios:`
            section. When set, the step runs once per scenario, with the
            scenario's values substituted into this step's configuration (see
            `expand_scenarios()`).

    """

    depends: list[str] = Field(default_factory=list)
    scenario: str | None = None

    def execute(self, *, dry_run: bool = False, force: bool = False) -> None:
        """
        Execute a processing step.

        A step whose target is already satisfied is skipped, so re-running a
        pipeline costs nothing rather than repeating work. `force` overrides
        that, giving a target the three states it needs: absent, present, and
        present-with-force.

        Args:
            dry_run: If True, the process will not actually execute but will simulate
                execution.
            force: If True, run even when `is_satisfied()` reports that the
                target is already present.

        Raises:
            Flepimop2ValidationError: If validation fails during a dry run.
        """
        if dry_run and (result := self._process_validate()) is not None:
            if result:
                raise Flepimop2ValidationError(result)
            return None
        if not force and self.is_satisfied():
            return None
        return self._process(dry_run=dry_run)

    def is_satisfied(self) -> bool:  # noqa: PLR6301
        """
        Report whether this step's target already exists.

        Override this in a module that produces a durable target (a fetched
        file, a transformed dataset) so that re-running the pipeline skips work
        already done. The default is `False`, i.e. always run, which is correct
        for a step with no persistent target.

        Core deliberately does not inspect the target itself: only the module
        knows what it produces and what counts as fresh, so cache-freshness and
        provenance policy live with the provider rather than here.

        Returns:
            True if the step can be skipped, otherwise False.

        """
        return False

    @abstractmethod
    def _process(self, *, dry_run: bool) -> None:
        """Backend-specific implementation for processing data."""
        ...

    def _process_validate(self) -> list[ValidationIssue] | None:  # noqa: PLR6301
        """
        Process validation hook.

        Returns:
            A boolean indicating if the process is valid, or `None` if not implemented.

        """
        return None


def build(config: dict[str, Any] | ModuleBase | str) -> ProcessABC:
    """Build a `ProcessABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary. The dict should contain a
            'module' key, which will be used to lookup the Process module path.
            The module will have "flepimop2.process." prepended.

    Returns:
        ProcessABC: The constructed process object.

    """
    return _build(config, "process", ProcessABC)  # type: ignore[type-abstract]


def _declared_depends(entry: object) -> list[str]:
    """
    Read the `depends` list off a raw process configuration entry.

    Read from the configuration rather than from a built `ProcessABC` so that
    the whole graph can be validated before any module is imported: a typo in a
    `depends` name should not require every module in the section to load first.

    Args:
        entry: A single process configuration entry.

    Returns:
        The declared dependency names, or an empty list when none are declared.

    """
    if isinstance(entry, ModuleBase):
        return list(getattr(entry, "depends", []) or [])
    if isinstance(entry, dict):
        declared = entry.get("depends") or []
        return [declared] if isinstance(declared, str) else list(declared)
    return []


def _declared_scenario(entry: object) -> str | None:
    """
    Read the `scenario` name off a raw process configuration entry.

    Read from the configuration for the same reason as `_declared_depends()`:
    every reference can then be checked before any module is imported.

    Args:
        entry: A single process configuration entry.

    Returns:
        The declared scenario name, or `None` when the step declares none.

    """
    if isinstance(entry, ModuleBase):
        declared = getattr(entry, "scenario", None)
    elif isinstance(entry, dict):
        declared = entry.get("scenario")
    else:
        return None
    return declared if isinstance(declared, str) and declared else None


def _substitute(value: object, values: Mapping[str, object]) -> object:
    """
    Rewrite `{name}` placeholders in a configuration value.

    Only the scenario's own names are substituted, and all placeholders are
    matched from the original string before replacement. Replacement values are
    therefore not recursively interpreted as placeholders. Braces that are not
    a scenario name survive untouched, which matters because process steps are
    frequently shell commands, where `awk '{print $1}'` is ordinary text rather
    than a template.

    A placeholder always resolves to text, even when it spans the whole value.
    Substituting the raw object instead would look tidier but breaks on the
    commonest field there is: a number dropped into a `list[str]` is rejected by
    the module's own validation, whereas text is coerced back to whatever the
    field declares (`"3"` into an `int` field is an `int`).

    Args:
        value: The configuration value to rewrite.
        values: The scenario's names and their values.

    Returns:
        The value with any placeholders resolved.

    Examples:
        >>> from flepimop2.process.abc import _substitute
        >>> _substitute("run --beta {beta}", {"beta": 0.3})
        'run --beta 0.3'
        >>> _substitute(["--n", "{n}"], {"n": 3})
        ['--n', '3']
        >>> _substitute("awk '{print $1}'", {"beta": 0.3})
        "awk '{print $1}'"

    """
    if isinstance(value, dict):
        return {key: _substitute(item, values) for key, item in value.items()}
    if isinstance(value, list):
        return [_substitute(item, values) for item in value]
    if not isinstance(value, str):
        return value

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        return str(values[name]) if name in values else match.group(0)

    return _PLACEHOLDER_PATTERN.sub(replace, value)


def _scenario_issues(
    section: dict[str, Any],
    scenarios: Mapping[str, Any],
) -> list[ValidationIssue]:
    """
    Collect every bad `scenario` reference in a process section.

    Args:
        section: The `process` configuration section.
        scenarios: The top-level `scenarios` section.

    Returns:
        One issue per step naming a scenario that does not exist.

    """
    return [
        ValidationIssue(
            msg=f"Process step '{name}' names unknown scenario '{declared}'.",
            kind="unknown_scenario",
            ctx={"step": name, "scenario": declared, "known": sorted(scenarios)},
        )
        for name, entry in section.items()
        if (declared := _declared_scenario(entry)) is not None
        and declared not in scenarios
    ]


def validate_scenarios(
    section: dict[str, Any],
    scenarios: Mapping[str, Any],
) -> None:
    """
    Check that every step's `scenario` names a defined scenario.

    Run before executing a plan, so that a typo costs nothing rather than
    surfacing partway through a pipeline. All bad references are reported
    together, matching how `resolve_plan()` reports `depends` problems.

    Args:
        section: The `process` configuration section.
        scenarios: The top-level `scenarios` section.

    Raises:
        Flepimop2ValidationError: If any step names a scenario that is not
            defined.

    """
    if issues := _scenario_issues(section, scenarios):
        raise Flepimop2ValidationError(issues)


def expand_scenarios(
    entry: dict[str, Any] | ModuleBase | str,
    scenarios: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """
    Expand one process step into the configurations it should run as.

    A step without a `scenario` yields its own configuration unchanged, so the
    unparameterized case stays exactly as it was. A step naming a scenario
    yields one configuration per scenario tuple, with that tuple's values
    substituted into the step's non-structural fields (see `_substitute()`).

    The fan-out deliberately happens *within* a plan step rather than by
    multiplying plan entries: `depends` names steps, so keeping a step a single
    node means a downstream step runs after every scenario of what it depends
    on, and the dependency contract needs no notion of a per-scenario edge.

    Args:
        entry: A single process configuration entry.
        scenarios: The top-level `scenarios` section.

    Returns:
        The configurations to execute, in scenario order.

    Raises:
        Flepimop2ValidationError: If the step names a scenario that is not
            defined.

    """
    config = _as_dict(entry) if not isinstance(entry, str) else {"module": entry}
    declared = _declared_scenario(entry)
    if declared is None:
        return [config]
    if declared not in scenarios:
        raise Flepimop2ValidationError([
            ValidationIssue(
                msg=f"Process step names unknown scenario '{declared}'.",
                kind="unknown_scenario",
                ctx={"scenario": declared, "known": sorted(scenarios)},
            )
        ])

    scenario = build_scenario(scenarios[declared])
    expanded: list[dict[str, Any]] = []
    for tuple_ in scenario.scenarios():
        values = tuple_._asdict()
        expanded.append({
            key: value if key in _STRUCTURAL_KEYS else _substitute(value, values)
            for key, value in config.items()
        })
    return expanded


def _depends_issues(depends: dict[str, list[str]]) -> list[ValidationIssue]:
    """
    Collect every problem with the declared dependency references.

    Every reference is checked rather than stopping at the first bad one, so a
    mis-wired configuration takes a single pass to fix.

    Args:
        depends: Mapping of step name to the names it declares a dependency on.

    Returns:
        One issue per bad reference; empty when the references are sound.

    """
    issues: list[ValidationIssue] = []
    for name, upstream in depends.items():
        for dep in upstream:
            if dep == name:
                issues.append(
                    ValidationIssue(
                        msg=f"Process step '{name}' depends on itself.",
                        kind="self_dependency",
                        ctx={"step": name},
                    )
                )
            elif dep not in depends:
                issues.append(
                    ValidationIssue(
                        msg=f"Process step '{name}' depends on unknown step '{dep}'.",
                        kind="unknown_dependency",
                        ctx={"step": name, "depends": dep, "known": sorted(depends)},
                    )
                )
    return issues


def _narrow_to_target(
    depends: dict[str, list[str]],
    target: str,
) -> dict[str, list[str]]:
    """
    Reduce the graph to a target and everything it transitively needs.

    Args:
        depends: Mapping of step name to the names it declares a dependency on.
        target: The step being planned for.

    Returns:
        The subgraph containing `target` and its transitive dependencies.

    Raises:
        KeyError: If `target` is not a step in the graph.

    """
    if target not in depends:
        msg = f"Process step '{target}' not found in {sorted(depends)}."
        raise KeyError(msg)
    wanted: set[str] = set()
    stack = [target]
    while stack:
        name = stack.pop()
        if name in wanted:
            continue
        wanted.add(name)
        stack.extend(depends[name])
    return {name: up for name, up in depends.items() if name in wanted}


def _topological_order(depends: dict[str, list[str]]) -> list[str]:
    """
    Order steps so that each one follows everything it depends on.

    Kahn's algorithm over the declared edges. Ties are broken by the order the
    steps appear in the configuration, so a plan is reproducible between runs
    and reads the way the file does.

    Args:
        depends: Mapping of step name to the names it declares a dependency on.

    Returns:
        The step names in dependency order.

    Raises:
        Flepimop2ValidationError: If the declared dependencies form a cycle.

    """
    order = list(depends)
    remaining = {name: set(upstream) for name, upstream in depends.items()}
    plan: list[str] = []
    while remaining:
        ready = [name for name in order if name in remaining and not remaining[name]]
        if not ready:
            cycle = sorted(remaining)
            raise Flepimop2ValidationError([
                ValidationIssue(
                    msg=f"Process steps form a dependency cycle: {', '.join(cycle)}.",
                    kind="dependency_cycle",
                    ctx={"steps": cycle},
                )
            ])
        for name in ready:
            plan.append(name)
            del remaining[name]
        for upstream in remaining.values():
            upstream.difference_update(ready)
    return plan


def resolve_plan(
    section: dict[str, Any],
    target: str | None = None,
) -> list[str]:
    """
    Resolve a process configuration section into an execution order.

    Validates every `depends` reference, rejects cycles, and returns the step
    names in dependency order. When `target` is given, the plan is narrowed to
    that step and its transitive dependencies, so asking for one step still runs
    what it needs.

    All problems are collected and reported together, rather than failing on the
    first one, so a mis-wired configuration takes one pass to fix.

    A `target` that is not a step in `section` raises `KeyError`.

    Args:
        section: The `process` configuration section, mapping step name to entry.
        target: Optional step to plan for. `None` plans the whole section.

    Returns:
        Step names in an order where every step follows its dependencies.

    Raises:
        Flepimop2ValidationError: If a `depends` name is unknown, a step depends
            on itself, or the declared dependencies form a cycle.

    Examples:
        >>> from flepimop2.process.abc import resolve_plan
        >>> section = {
        ...     "transform": {"module": "shell", "depends": ["fetch"]},
        ...     "fetch": {"module": "shell"},
        ... }
        >>> resolve_plan(section)
        ['fetch', 'transform']
        >>> resolve_plan(section, target="fetch")
        ['fetch']

    """
    depends = {name: _declared_depends(entry) for name, entry in section.items()}
    if issues := _depends_issues(depends):
        raise Flepimop2ValidationError(issues)
    if target is not None:
        depends = _narrow_to_target(depends, target)
    return _topological_order(depends)
