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
"""Tests for process dependency declaration, planning, and the no-op contract."""

from typing import Any

import pytest

from flepimop2._utils._click import _click_param_for_option, _render_param
from flepimop2.cli._options import get_option
from flepimop2.cli._process_command import _should_force
from flepimop2.exceptions import Flepimop2ValidationError
from flepimop2.process.abc import ProcessABC, resolve_plan


def _step(depends: list[str] | None = None) -> dict[str, Any]:
    """
    Build a minimal process configuration entry.

    Args:
        depends: Optional dependency names to declare on the step.

    Returns:
        A process configuration entry.

    """
    config: dict[str, Any] = {"module": "shell", "command": "true"}
    if depends is not None:
        config["depends"] = depends
    return config


# --- planning -----------------------------------------------------------------


def test_resolve_plan_orders_dependencies_first() -> None:
    """A step is planned after everything it declares a dependency on."""
    section = {"transform": _step(["fetch"]), "fetch": _step()}
    assert resolve_plan(section) == ["fetch", "transform"]


def test_resolve_plan_orders_a_chain() -> None:
    """Transitive dependencies are ordered, not just direct ones."""
    section = {"c": _step(["b"]), "b": _step(["a"]), "a": _step()}
    assert resolve_plan(section) == ["a", "b", "c"]


def test_resolve_plan_without_dependencies_keeps_config_order() -> None:
    """Independent steps stay in the order the configuration lists them.

    Ties are broken by configuration order so a plan is reproducible between
    runs and reads the way the file does.
    """
    section = {"b": _step(), "a": _step(), "c": _step()}
    assert resolve_plan(section) == ["b", "a", "c"]


def test_resolve_plan_orders_multiple_dependencies_before_their_dependent() -> None:
    """A step with several dependencies runs after all of them.

    The dependencies are mutually independent, so their relative order is only
    required to follow the configuration; what must hold is that every one of
    them precedes the step that declares them.
    """
    section = {
        "combine": _step(["fetch_b", "fetch_a", "fetch_c"]),
        "fetch_a": _step(),
        "fetch_b": _step(),
        "fetch_c": _step(),
    }
    plan = resolve_plan(section)

    assert plan[-1] == "combine"
    # Independent steps keep configuration order rather than the order they
    # happen to be named in `depends`.
    assert plan[:-1] == ["fetch_a", "fetch_b", "fetch_c"]


def test_resolve_plan_orders_a_diamond() -> None:
    """A step reachable by two paths runs once, after both of them."""
    section = {
        "report": _step(["left", "right"]),
        "left": _step(["base"]),
        "right": _step(["base"]),
        "base": _step(),
    }
    plan = resolve_plan(section)

    assert plan.count("base") == 1
    assert plan.index("base") < plan.index("left")
    assert plan.index("base") < plan.index("right")
    assert plan.index("left") < plan.index("report")
    assert plan.index("right") < plan.index("report")


def test_resolve_plan_narrows_past_multiple_dependencies() -> None:
    """Narrowing to a step pulls in every branch it needs, and nothing else."""
    section = {
        "combine": _step(["fetch_a", "fetch_b"]),
        "fetch_a": _step(),
        "fetch_b": _step(),
        "unrelated": _step(),
    }
    plan = resolve_plan(section, target="combine")

    assert plan == ["fetch_a", "fetch_b", "combine"]
    assert "unrelated" not in plan


def test_resolve_plan_narrows_to_a_target_and_its_upstream() -> None:
    """Asking for one step plans that step plus what it needs, nothing else."""
    section = {
        "fetch": _step(),
        "transform": _step(["fetch"]),
        "unrelated": _step(),
    }
    assert resolve_plan(section, target="transform") == ["fetch", "transform"]
    assert resolve_plan(section, target="fetch") == ["fetch"]


def test_resolve_plan_accepts_a_scalar_depends() -> None:
    """A single dependency may be written without a list."""
    section = {"transform": {"module": "shell", "depends": "fetch"}, "fetch": _step()}
    assert resolve_plan(section) == ["fetch", "transform"]


def test_resolve_plan_of_an_empty_section_is_empty() -> None:
    """An empty process section plans nothing rather than erroring."""
    assert resolve_plan({}) == []


# --- validation ---------------------------------------------------------------


def test_resolve_plan_rejects_an_unknown_dependency() -> None:
    """A `depends` name that is not a sibling step is reported, with context."""
    with pytest.raises(Flepimop2ValidationError) as excinfo:
        resolve_plan({"transform": _step(["nope"])})
    issues = excinfo.value.issues
    assert len(issues) == 1
    assert issues[0].kind == "unknown_dependency"
    assert issues[0].ctx is not None
    assert issues[0].ctx["depends"] == "nope"


def test_resolve_plan_rejects_a_self_dependency() -> None:
    """A step depending on itself is its own error, not a generic cycle."""
    with pytest.raises(Flepimop2ValidationError) as excinfo:
        resolve_plan({"loop": _step(["loop"])})
    assert excinfo.value.issues[0].kind == "self_dependency"


def test_resolve_plan_rejects_a_cycle() -> None:
    """Mutually dependent steps are rejected before anything executes."""
    section = {"a": _step(["b"]), "b": _step(["a"])}
    with pytest.raises(Flepimop2ValidationError) as excinfo:
        resolve_plan(section)
    issue = excinfo.value.issues[0]
    assert issue.kind == "dependency_cycle"
    assert issue.ctx is not None
    assert issue.ctx["steps"] == ["a", "b"]


def test_resolve_plan_rejects_a_longer_cycle() -> None:
    """A cycle through an intermediate step is detected too."""
    section = {"a": _step(["c"]), "b": _step(["a"]), "c": _step(["b"])}
    with pytest.raises(Flepimop2ValidationError) as excinfo:
        resolve_plan(section)
    assert excinfo.value.issues[0].kind == "dependency_cycle"


def test_resolve_plan_reports_every_bad_reference_at_once() -> None:
    """All reference problems are collected, so one pass fixes the config."""
    section = {"a": _step(["missing_one"]), "b": _step(["missing_two"])}
    with pytest.raises(Flepimop2ValidationError) as excinfo:
        resolve_plan(section)
    kinds = [issue.kind for issue in excinfo.value.issues]
    assert kinds == ["unknown_dependency", "unknown_dependency"]


def test_resolve_plan_rejects_an_unknown_target() -> None:
    """Planning for a step that does not exist is a KeyError, not a bad plan."""
    with pytest.raises(KeyError):
        resolve_plan({"fetch": _step()}, target="nope")


# --- the no-op contract -------------------------------------------------------


class _CountingProcess(ProcessABC, module="counting"):
    """A process that records how many times it actually ran."""

    satisfied: bool = False
    runs: int = 0

    def is_satisfied(self) -> bool:
        """
        Report the satisfaction state this instance was configured with.

        Returns:
            Whether the step should be treated as already done.

        """
        return self.satisfied

    def _process(self, *, dry_run: bool) -> None:
        """Count a real execution."""
        if not dry_run:
            self.runs += 1


def test_execute_runs_when_the_target_is_absent() -> None:
    """The default contract is to run: no target, no skipping."""
    process = _CountingProcess(satisfied=False)
    process.execute()
    assert process.runs == 1


def test_execute_skips_when_the_target_is_satisfied() -> None:
    """A satisfied step is a no-op, which is what makes re-runs cheap."""
    process = _CountingProcess(satisfied=True)
    process.execute()
    assert process.runs == 0


def test_execute_force_overrides_satisfaction() -> None:
    """`force` is the third state: present, but run anyway."""
    process = _CountingProcess(satisfied=True)
    process.execute(force=True)
    assert process.runs == 1


def test_is_satisfied_defaults_to_false() -> None:
    """A step with no durable target always runs."""

    class _Plain(ProcessABC, module="plain"):
        def _process(self, *, dry_run: bool) -> None:  # noqa: ARG002
            return None

    assert _Plain().is_satisfied() is False


def test_depends_defaults_to_empty() -> None:
    """Declaring no dependencies is the common case and needs no config."""

    class _Plain2(ProcessABC, module="plain2"):
        def _process(self, *, dry_run: bool) -> None:  # noqa: ARG002
            return None

    assert _Plain2().depends == []


# --- the --force counter ------------------------------------------------------


@pytest.mark.parametrize(
    ("force", "expected"),
    [
        (0, (False, False)),
        (1, (True, False)),
        (2, (True, True)),
        (3, (True, True)),
    ],
)
def test_force_counter_selects_how_much_of_the_plan_is_forced(
    force: int,
    expected: tuple[bool, bool],
) -> None:
    """`-f` forces the requested step, `-ff` its dependencies as well.

    Separating the two keeps the common case cheap: re-running a transform
    should not re-download everything upstream of it unless asked.
    """
    target_forced, dependency_forced = expected
    assert _should_force(force, "transform", "transform") is target_forced
    assert _should_force(force, "fetch", "transform") is dependency_forced


def test_force_option_renders_back_to_repeated_short_flag() -> None:
    """A counted `--force` must survive being re-rendered as argv.

    Commands are re-dispatched to job backends by rendering their bound options
    back into tokens, and `_render_param` renders a counter using its *short*
    flag. Without `-f` the option would render as `-forceforce`, so the
    shorthand is what makes the counter round-trip.
    """
    param = _click_param_for_option(get_option("force"))
    assert param is not None
    assert "-f" in param.opts
    assert _render_param(param, 0) == []
    assert _render_param(param, 1) == ["-f"]
    assert _render_param(param, 2) == ["-ff"]
