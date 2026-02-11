"""Private module for working with parameters and parameter groups."""

__all__ = ["ParameterCollection"]


from collections.abc import Iterable

import numpy as np
from numpy.typing import NDArray

from flepimop2.configuration._module import ModuleGroupModel
from flepimop2.configuration._types import IdentifierString
from flepimop2.parameter.abc import ParameterABC
from flepimop2.parameter.abc import build as build_parameter


def _param_maps_to_alias(
    param_name: IdentifierString,
    aliases: set[IdentifierString],
    groups: dict[IdentifierString, dict[IdentifierString, IdentifierString]],
    group_names: Iterable[IdentifierString],
) -> bool:
    """
    Check if param maps to an alias in non-selected groups.

    Args:
        param_name: The original parameter name to check.
        aliases: Set of aliases created by selected groups.
        groups: Dictionary mapping group names to parameter rename mappings.
        group_names: List of group names that are selected.

    Returns:
        True if the parameter maps to an alias, False otherwise.

    """
    for group_name, group_mapping in groups.items():
        if group_name in group_names:
            continue
        for alias, source in group_mapping.items():
            if source == param_name and alias in aliases:
                return True
    return False


def _resolve_final_parameter_name_mapping(
    groups: dict[IdentifierString, dict[IdentifierString, IdentifierString]],
    parameters: ModuleGroupModel,
    group_names: Iterable[IdentifierString],
) -> dict[IdentifierString, IdentifierString]:
    """
    Resolve the final parameter name mapping based on selected groups.

    This function builds the final parameter name mapping by:

    1. Applying renaming from selected groups
    2. Adding identity mappings for parameters not excluded by group selection

    Parameters are excluded from identity mapping if they would map to an alias
    that was created by a selected group in a non-selected group.

    Args:
        groups: Dictionary mapping group names to parameter rename mappings.
        parameters: Dictionary of parameter configurations.
        group_names: List of group names to apply for parameter renaming.

    Returns:
        The final parameter name mapping.

    """
    final_mapping: dict[IdentifierString, IdentifierString] = {}
    for group_name in group_names:
        final_mapping.update(groups[group_name])
    aliases_created = set(final_mapping.keys())
    parameters_used = set(final_mapping.values())
    final_mapping.update({
        p: p
        for p in parameters
        if p not in parameters_used
        and not _param_maps_to_alias(p, aliases_created, groups, group_names)
    })
    return final_mapping


class ParameterCollection:
    """
    Parameter collection with support for groups.

    This class takes parameter configurations, group mappings, and a list of
    group names to apply. It validates the configuration, pre-builds only the
    needed parameters, and efficiently samples them with group-based renaming.

    Validations:
        - All group names in `group_names` must exist in `groups`.
        - No two groups can rename different parameters to the same target name.
        - All conflicts are reported before raising an error.

    Optimizations:
        - Parameters are pre-built during initialization.
        - Only parameters actually used by the selected groups are built.
        - The final renaming mapping is pre-computed.

    Examples:
        >>> from flepimop2._parameters import ParameterCollection
        >>> from flepimop2.configuration import ModuleModel
        >>> parameters = {
        ...     "beta_high": ModuleModel(module="fixed", value=0.8),
        ...     "beta_low": ModuleModel(module="fixed", value=0.2),
        ...     "gamma": ModuleModel(module="fixed", value=0.1),
        ... }
        >>> groups = {
        ...     "high_transmission": {"beta": "beta_high"},
        ...     "low_transmission": {"beta": "beta_low"},
        ... }
        >>> collection_high = ParameterCollection(
        ...     parameters=parameters,
        ...     groups=groups,
        ...     group_names=["high_transmission"],
        ... )
        >>> sorted(collection_high.parameter_names)
        ['beta', 'gamma']
        >>> realization = collection_high.realize()
        >>> {k: realization[k] for k in sorted(realization.keys())}
        {'beta': array([0.8]), 'gamma': array([0.1])}
        >>> collection_low = ParameterCollection(
        ...     parameters=parameters,
        ...     groups=groups,
        ...     group_names=["low_transmission"],
        ... )
        >>> sorted(collection_low.parameter_names)
        ['beta', 'gamma']
        >>> realization = collection_low.realize()
        >>> {k: realization[k] for k in sorted(realization.keys())}
        {'beta': array([0.2]), 'gamma': array([0.1])}
        >>> collection = ParameterCollection(
        ...     parameters=parameters,
        ...     groups=groups,
        ... )
        >>> sorted(collection.parameter_names)
        ['beta_high', 'beta_low', 'gamma']
        >>> realization = collection.realize()
        >>> {k: realization[k] for k in sorted(realization.keys())}
        {'beta_high': array([0.8]), 'beta_low': array([0.2]), 'gamma': array([0.1])}

    """

    def __init__(
        self,
        parameters: ModuleGroupModel,
        groups: dict[IdentifierString, dict[IdentifierString, IdentifierString]],
        group_names: Iterable[IdentifierString] | None = None,
    ) -> None:
        """
        Initialize the ParameterCollection.

        Args:
            parameters: Dictionary of parameter configurations from ConfigurationModel.
            groups: Dictionary mapping group names to parameter rename mappings.
                Each group maps new parameter names to their original names.
            group_names: An iterable of group names to apply for parameter renaming.

        """
        self._parameters = parameters
        self._groups = groups
        self._group_names = group_names or []
        self._validate_group_names()
        self._validate_no_conflicts()
        self._final_mapping = _resolve_final_parameter_name_mapping(
            self._groups, self._parameters, self._group_names
        )
        self._built_parameters: dict[IdentifierString, ParameterABC] = {
            target: build_parameter(self._parameters[source])
            for target, source in self._final_mapping.items()
        }

    def _validate_group_names(self) -> None:
        """
        Validate that all group names exist in groups.

        Raises:
            ValueError: If any group names are not found in groups.

        """
        missing_groups = set(self._group_names) - set(self._groups.keys())
        if missing_groups:
            msg = (
                f"Group names not found in groups: {sorted(missing_groups)}. "
                f"Available groups: {sorted(self._groups.keys())}."
            )
            raise ValueError(msg)

    def _validate_no_conflicts(self) -> None:
        """
        Validate that there are no parameter renaming conflicts.

        Raises:
            ValueError: If there are parameter renaming conflicts.

        """
        target_to_sources: dict[
            IdentifierString, list[tuple[IdentifierString, IdentifierString]]
        ] = {}
        for group_name in self._group_names:
            group_mapping = self._groups[group_name]
            for target, source in group_mapping.items():
                if target not in target_to_sources:
                    target_to_sources[target] = []
                target_to_sources[target].append((source, group_name))

        conflicts: dict[
            IdentifierString, list[tuple[IdentifierString, IdentifierString]]
        ] = {}
        for target, sources_list in target_to_sources.items():
            unique_sources = {source for source, _ in sources_list}
            if len(unique_sources) > 1:
                conflicts[target] = sources_list

        if conflicts:
            conflict_details = []
            for target in sorted(conflicts.keys()):
                sources_list = conflicts[target]
                details = ", ".join(
                    f"'{source}' from group '{group}'" for source, group in sources_list
                )
                conflict_details.append(f"  '{target}' is mapped from: {details}")
            msg = "Parameter renaming conflicts detected:\n" + "\n".join(
                conflict_details
            )
            raise ValueError(msg)

    @property
    def parameter_names(self) -> set[IdentifierString]:
        """
        Get the set of final parameter names after applying groups.

        Returns:
            Set of final parameter names.

        """
        return set(self._final_mapping.keys())

    def realize(
        self, subset: set[IdentifierString] | None = None
    ) -> dict[IdentifierString, NDArray[np.float64]]:
        """
        Realize parameters by sampling pre-built parameters and applying renaming.

        This method samples from the pre-built parameters (constructed during
        initialization) and applies the pre-computed group-based renaming.

        Args:
            subset: Optional set of parameter names to include in the output.
                If provided, only these parameters will be included.

        Returns:
            A dictionary mapping parameter names (after renaming) to their
            sampled values as float64 NumPy arrays.

        """
        subset = subset or self.parameter_names
        return {target: self._built_parameters[target].sample() for target in subset}
