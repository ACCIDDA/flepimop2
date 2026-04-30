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
"""Tests for `_build` via the public module builders."""

from collections.abc import Callable
from typing import Any

import pytest

from flepimop2.backend.abc import build as build_backend
from flepimop2.configuration import ModuleModel
from flepimop2.engine.abc import build as build_engine
from flepimop2.module import ModuleABC
from flepimop2.parameter.abc import build as build_parameter
from flepimop2.process.abc import build as build_process
from flepimop2.scenario.abc import build as build_scenario
from flepimop2.system.abc import build as build_system


@pytest.mark.parametrize(
    ("builder", "namespace"),
    [
        (build_backend, "backend"),
        (build_engine, "engine"),
        (build_parameter, "parameter"),
        (build_process, "process"),
        (build_scenario, "scenario"),
        (build_system, "system"),
    ],
)
def test_build_requires_explicit_module(
    builder: Callable[[dict[str, Any] | ModuleModel], ModuleABC],
    namespace: str,
) -> None:
    """Each public builder should require an explicit `module`."""
    with pytest.raises(
        ValueError,
        match=(
            rf"Configuration for namespace '{namespace}' must define a non-empty "
            r"'module' string\."
        ),
    ):
        builder({})
