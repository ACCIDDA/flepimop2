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
from collections.abc import Mapping
from copy import deepcopy
from importlib import import_module
from typing import Final, Literal, Self

from pydantic import BaseModel, Field, model_validator

from flepimop2._utils._dict import _deep_merge_dicts
from flepimop2.configuration._axes import AxesGroupModel
from flepimop2.configuration._module import ModuleGroupModel, ParameterGroupModel
from flepimop2.configuration._simulate import SimulateSpecificationModel
from flepimop2.configuration._yaml import YamlSerializableBaseModel
from flepimop2.module import ModuleBase
from flepimop2.typing import IdentifierString, PatchConflictMode

_CONFIGURATION_SECTION_ORDER: Final[tuple[str, ...]] = (
    "name",
    "axes",
    "engines",
    "systems",
    "backends",
    "jobs",
    "process",
    "parameters",
    "scenarios",
    "simulate",
)
_LIST_VIEW_SECTIONS: Final[tuple[str, ...]] = (
    "engines",
    "systems",
    "backends",
    "jobs",
    "process",
    "parameters",
    "scenarios",
)


class ConfigurationModel(
    YamlSerializableBaseModel,
    alias_generator=lambda name: name.removesuffix("s"),
    validate_by_name=True,
):
    """
    Configuration model for flepimop2.

    This model serves as the parent container for a parsed configuration file.

    Attributes:
        name: An optional name for the configuration.
        engines: A dictionary of engine configurations.
        systems: A dictionary of system configurations.
        backends: A dictionary of backend configurations.
        process: A dictionary of process configurations.
        parameters: A dictionary of parameter configurations.
        simulate: A dictionary of simulation configurations.
    """

    name: str | None = None
    axes: AxesGroupModel = Field(default_factory=dict)
    engines: ModuleGroupModel = Field(default_factory=dict)
    systems: ModuleGroupModel = Field(default_factory=dict)
    backends: ModuleGroupModel = Field(default_factory=dict)
    process: ModuleGroupModel = Field(default_factory=dict)
    parameters: ParameterGroupModel = Field(default_factory=dict)
    scenarios: ModuleGroupModel = Field(default_factory=dict)
    jobs: ModuleGroupModel = Field(default_factory=dict)
    simulate: dict[IdentifierString, SimulateSpecificationModel] = Field(
        default_factory=dict
    )

    def to_yaml_data(self) -> object:
        """
        Convert the configuration into its normalized YAML representation.

        This preserves parsing/patching semantics while allowing the emitted
        YAML to use a more compact, user-facing structure.

        Returns:
            A YAML-ready representation of the configuration.
        """
        data = super().to_yaml_data()
        if not isinstance(data, dict):
            return data

        if not data.get("name"):
            data.pop("name", None)

        if self.parameters:
            build_parameter = import_module("flepimop2.parameter.abc").build
            data["parameters"] = {
                name: build_parameter(parameter).to_yaml_data()
                if isinstance(parameter, ModuleBase | str)
                else parameter
                for name, parameter in self.parameters.items()
            }

        ordered_data = {}
        if name := data.get("name"):
            ordered_data["name"] = name

        for section_name in _CONFIGURATION_SECTION_ORDER[1:]:
            if not (section := data.get(section_name)):
                continue
            if (
                section_name in _LIST_VIEW_SECTIONS
                and isinstance(section, dict)
                and len(section) == 1
                and "default" in section
            ):
                section = [section["default"]]
            ordered_data[section_name] = section

        ordered_data.update({
            key: value
            for key, value in data.items()
            if key not in _CONFIGURATION_SECTION_ORDER
        })
        return ordered_data

    @staticmethod
    def _copy_patch_value(value: object) -> object:
        """
        Create a deep copy suitable for a patched configuration value.

        Args:
            value: The value to copy.

        Returns:
            A deep copy of `value`.
        """
        if isinstance(value, BaseModel):
            return value.model_copy(deep=True)
        return deepcopy(value)

    @staticmethod
    def _collect_patch_conflicts(
        current: Mapping[IdentifierString, object],
        patch: Mapping[IdentifierString, object],
    ) -> list[IdentifierString]:
        """
        Collect duplicate keys shared by two configuration sections.

        Args:
            current: The current section contents.
            patch: The incoming section patch.

        Returns:
            The sorted list of conflicting keys.
        """
        return sorted(set(current) & set(patch))

    @staticmethod
    def _patch_section(
        current: Mapping[IdentifierString, object],
        patch: Mapping[IdentifierString, object],
        *,
        conflict: PatchConflictMode,
    ) -> dict[IdentifierString, object]:
        """
        Patch one top-level dictionary section of the configuration.

        Args:
            current: The current section contents.
            patch: The incoming section patch.
            conflict: How to handle duplicate entry names.

        Returns:
            The patched section contents.

        Raises:
            AssertionError: If overlapping entries reach this method under
                `conflict="error"`.
        """
        patched = {
            key: ConfigurationModel._copy_patch_value(value)
            for key, value in current.items()
        }
        for key, patch_value in patch.items():
            if key not in patched:
                patched[key] = ConfigurationModel._copy_patch_value(patch_value)
                continue
            if conflict is PatchConflictMode.REPLACE:
                if isinstance(current_value := patched[key], ModuleBase) and isinstance(
                    patch_value, ModuleBase
                ):
                    patched[key] = current_value.patch(
                        patch_value,
                        conflict=conflict,
                    )
                else:
                    patched[key] = ConfigurationModel._copy_patch_value(patch_value)
                continue
            if conflict is PatchConflictMode.ERROR:
                msg = (
                    "ConfigurationModel.patch should reject duplicate keys before "
                    "_patch_section processes overlapping entries."
                )
                raise AssertionError(msg)
            current_value = patched[key]
            if isinstance(current_value, ModuleBase) and isinstance(
                patch_value, ModuleBase
            ):
                patched[key] = current_value.patch(
                    patch_value,
                    conflict=PatchConflictMode.MERGE,
                )
            elif isinstance(current_value, BaseModel) and isinstance(
                patch_value, BaseModel
            ):
                if type(current_value) is not type(patch_value):
                    patched[key] = ConfigurationModel._copy_patch_value(patch_value)
                else:
                    patched[key] = type(current_value).model_validate(
                        _deep_merge_dicts(
                            current_value.model_dump(),
                            patch_value.model_dump(),
                        )
                    )
            else:
                patched[key] = ConfigurationModel._copy_patch_value(patch_value)
        return patched

    def patch(
        self,
        other: Self,
        *,
        conflict: PatchConflictMode = PatchConflictMode.ERROR,
    ) -> Self:
        """
        Patch this configuration with another configuration.

        This method treats `other` as the incoming patch. Top-level sections are
        merged entry-by-entry; when both entries are `ModuleBase` instances their
        `patch()` implementations are used.

        Args:
            other: The patch to apply to this configuration.
            conflict: How to handle duplicate top-level entry names.

        Returns:
            The patched configuration.

        Raises:
            ValueError: If there are sub-top level key conflicts and `conflict` is
                `PatchConflictMode.ERROR`.
        """
        section_conflicts = {
            section_name: self._collect_patch_conflicts(
                getattr(self, section_name),
                getattr(other, section_name),
            )
            for section_name in (
                "axes",
                "engines",
                "systems",
                "backends",
                "process",
                "parameters",
                "scenarios",
                "jobs",
                "simulate",
            )
        }
        section_conflicts = {
            section_name: conflicts
            for section_name, conflicts in section_conflicts.items()
            if conflicts
        }
        if conflict is PatchConflictMode.ERROR and section_conflicts:
            details = "; ".join(
                f"{section_name}={conflicts!r}"
                for section_name, conflicts in section_conflicts.items()
            )
            msg = (
                "Cannot patch configuration under conflict='error'; duplicate "
                f"section keys: {details}."
            )
            raise ValueError(msg)

        sections = {
            "axes": self._patch_section(
                self.axes,
                other.axes,
                conflict=conflict,
            ),
            "engines": self._patch_section(
                self.engines,
                other.engines,
                conflict=conflict,
            ),
            "systems": self._patch_section(
                self.systems,
                other.systems,
                conflict=conflict,
            ),
            "backends": self._patch_section(
                self.backends,
                other.backends,
                conflict=conflict,
            ),
            "process": self._patch_section(
                self.process,
                other.process,
                conflict=conflict,
            ),
            "parameters": self._patch_section(
                self.parameters,
                other.parameters,
                conflict=conflict,
            ),
            "scenarios": self._patch_section(
                self.scenarios,
                other.scenarios,
                conflict=conflict,
            ),
            "jobs": self._patch_section(
                self.jobs,
                other.jobs,
                conflict=conflict,
            ),
            "simulate": self._patch_section(
                self.simulate,
                other.simulate,
                conflict=conflict,
            ),
        }

        name_payload: dict[str, str | None] = {}
        if "name" in other.model_fields_set:
            name_payload["name"] = other.name
        elif "name" in self.model_fields_set:
            name_payload["name"] = self.name

        patched = type(self).model_validate({**name_payload, **sections})
        patched.set_document_start_marker(
            value=self.document_start_marker or other.document_start_marker
        )
        return patched

    def _check_simulate_engines_or_systems(
        self, kind: Literal["engine", "system", "backend"]
    ) -> None:
        """
        Ensure that all engines/systems/backends referenced in simulate exist.

        Args:
            kind: Either "engine", "system", or "backend" to specify which to check.

        Raises:
            ValueError: If any referenced engines or systems are not defined.
        """
        items = {getattr(sim, kind) for sim in self.simulate.values()}
        defined = set(getattr(self, f"{kind}s").keys())
        if missing := items - defined:
            msg = (
                f"{kind}s referenced in simulate not defined: "
                f"{missing}. Available {kind}s: {defined}"
            )
            raise ValueError(msg)

    @model_validator(mode="after")
    def _check_simulate_engines(self) -> Self:
        """
        Ensure that all engines referenced in simulate exist.

        Returns:
            The validated `ConfigurationModel` instance.

        Examples:
            >>> from flepimop2.configuration import ConfigurationModel
            >>> config = {
            ...     "engines": {
            ...         "foo": {"module": "test"},
            ...     },
            ...     "systems": {
            ...         "bar": {"module": "test"},
            ...     },
            ...     "backends": {
            ...         "csv": {"module": "test"},
            ...     },
            ...     "simulate": {
            ...         "sim1": {
            ...             "engine": "fizz",
            ...             "system": "bar",
            ...             "backend": "csv",
            ...             "times": [1.0, 2.0, 3.0],
            ...         },
            ...     },
            ... }
            >>> ConfigurationModel.model_validate(config)
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for ConfigurationModel
              Value error, engines referenced in simulate not defined: {'fizz'}. Available engines: {'foo'} [...]
                For further information visit ...
        """  # noqa: E501
        self._check_simulate_engines_or_systems("engine")
        return self

    @model_validator(mode="after")
    def _check_simulate_systems(self) -> Self:
        """
        Ensure that all systems referenced in simulate exist.

        Returns:
            The validated `ConfigurationModel` instance.

        Examples:
            >>> from flepimop2.configuration import ConfigurationModel
            >>> config = {
            ...     "engines": {
            ...         "foo": {"module": "test"},
            ...     },
            ...     "systems": {
            ...         "bar": {"module": "test"},
            ...     },
            ...     "backends": {
            ...         "csv": {"module": "test"},
            ...     },
            ...     "simulate": {
            ...         "sim1": {
            ...             "engine": "foo",
            ...             "system": "buzz",
            ...             "backend": "csv",
            ...             "times": [1.0, 2.0, 3.0],
            ...         },
            ...     },
            ... }
            >>> ConfigurationModel.model_validate(config)
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for ConfigurationModel
              Value error, systems referenced in simulate not defined: {'buzz'}. Available systems: {'bar'} [...]
                For further information visit ...
        """  # noqa: E501
        self._check_simulate_engines_or_systems("system")
        return self

    @model_validator(mode="after")
    def _check_simulate_backends(self) -> Self:
        """
        Ensure that all backends referenced in simulate exist.

        Returns:
            The validated `ConfigurationModel` instance.

        Examples:
            >>> from flepimop2.configuration import ConfigurationModel
            >>> config = {
            ...     "engines": {
            ...         "foo": {"module": "test"},
            ...     },
            ...     "systems": {
            ...         "bar": {"module": "test"},
            ...     },
            ...     "backends": {
            ...         "csv": {"module": "test"},
            ...     },
            ...     "simulate": {
            ...         "sim1": {
            ...             "engine": "foo",
            ...             "system": "bar",
            ...             "backend": "db",
            ...             "times": [1.0, 2.0, 3.0],
            ...         },
            ...     },
            ... }
            >>> configuration = ConfigurationModel.model_validate(config)
            Traceback (most recent call last):
                ...
            pydantic_core._pydantic_core.ValidationError: 1 validation error for ConfigurationModel
              Value error, backends referenced in simulate not defined: {'db'}. Available backends: {'csv'} [...]
                For further information visit ...
        """  # noqa: E501
        self._check_simulate_engines_or_systems("backend")
        return self
