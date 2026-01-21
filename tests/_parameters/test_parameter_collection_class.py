"""Unit tests for the `ParameterCollection` class."""

import re
from typing import Any

import pytest

from flepimop2._parameters import ParameterCollection
from flepimop2.configuration import IdentifierString, ModuleGroupModel


@pytest.fixture
def basic_parameters() -> dict[str, Any]:
    """Basic parameter configurations for testing.

    Returns:
        A dictionary of parameter configurations with fixed values.
    """
    return {
        "param1": {"module": "flepimop2.parameter.fixed", "value": 1.0},
        "param2": {"module": "flepimop2.parameter.fixed", "value": 2.0},
        "param3": {"module": "flepimop2.parameter.fixed", "value": 3.0},
        "param4": {"module": "flepimop2.parameter.fixed", "value": 4.0},
    }


@pytest.fixture
def basic_groups() -> dict[str, Any]:
    """Basic group configurations for testing.

    Returns:
        A dictionary mapping group names to parameter rename mappings.
    """
    return {
        "group1": {
            "renamed_a": "param1",
            "renamed_b": "param2",
        },
        "group2": {
            "renamed_c": "param3",
            "renamed_d": "param4",
        },
    }


@pytest.mark.parametrize(
    ("groups", "parameters", "group_names", "missing_group_names"),
    [
        (
            {"group1": {"reparam1": "param1"}},
            {"param1": {"module": "fixed", "value": 1.0}},
            ["nonexistent_group"],
            ["nonexistent_group"],
        ),
        (
            {"group1": {"reparam1": "param1"}},
            {"param1": {"module": "fixed", "value": 1.0}},
            ["group1", "missing_group"],
            ["missing_group"],
        ),
        (
            {"group1": {"reparam1": "param1"}, "group2": {"reparam2": "param1"}},
            {"param1": {"module": "fixed", "value": 1.0}},
            ["missing_group", "group2"],
            ["missing_group"],
        ),
        (
            {"group1": {"reparam1": "param1"}, "group2": {"reparam2": "param2"}},
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
            },
            ["group1", "missing_group", "group2", "another_missing_group"],
            ["missing_group", "another_missing_group"],
        ),
        (
            {},
            {"param1": {"module": "fixed", "value": 1.0}},
            ["missing_group"],
            ["missing_group"],
        ),
    ],
)
def test_group_names_not_found_in_groups_value_error(
    groups: dict[IdentifierString, dict[IdentifierString, IdentifierString]],
    parameters: ModuleGroupModel,
    group_names: list[IdentifierString],
    missing_group_names: list[IdentifierString],
) -> None:
    """Test that ValueError is raised when group names are not found in groups."""
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Group names not found in groups: "
            f"{sorted(missing_group_names)}. "
            "Available groups:"
        ),
    ):
        ParameterCollection(parameters, groups, group_names)


@pytest.mark.parametrize(
    ("groups", "parameters", "group_names", "conflicting_renames"),
    [
        (
            {"group_a": {"paramX": "param1"}, "group_b": {"paramX": "param2"}},
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
            },
            ["group_a", "group_b"],
            {"paramX": [("param1", "group_a"), ("param2", "group_b")]},
        ),
        (
            {
                "group1": {"p": "param1"},
                "group2": {"p": "param2"},
                "group3": {"p": "param3"},
            },
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
                "param3": {"module": "fixed", "value": 3.0},
            },
            ["group1", "group2", "group3"],
            {"p": [("param1", "group1"), ("param2", "group2"), ("param3", "group3")]},
        ),
        (
            {
                "group1": {"p": "param1"},
                "group2": {"p": "param2"},
                "group3": {"p": "param3"},
            },
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
                "param3": {"module": "fixed", "value": 3.0},
            },
            ["group2", "group3"],
            {"p": [("param2", "group2"), ("param3", "group3")]},
        ),
        (
            {
                "groupA": {"x": "param1", "y": "param2"},
                "groupB": {"y": "param3", "z": "param4"},
            },
            {
                "x": {"module": "fixed", "value": 1.0},
                "y": {"module": "fixed", "value": 2.0},
                "z": {"module": "fixed", "value": 3.0},
            },
            ["groupA", "groupB"],
            {"y": [("param2", "groupA"), ("param3", "groupB")]},
        ),
        (
            {
                "group_1": {"a": "param1", "b": "param2"},
                "group_2": {"a": "param3", "b": "param4"},
                "group_a": {"b": "param5"},
            },
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
                "param3": {"module": "fixed", "value": 3.0},
                "param4": {"module": "fixed", "value": 4.0},
                "param5": {"module": "fixed", "value": 5.0},
            },
            ["group_1", "group_2", "group_a"],
            {
                "a": [("param1", "group_1"), ("param3", "group_2")],
                "b": [
                    ("param2", "group_1"),
                    ("param4", "group_2"),
                    ("param5", "group_a"),
                ],
            },
        ),
        (
            {
                "group_a": {"a": "param1"},
                "group_b": {"a": "param2"},
                "group_c": {"b": "param3"},
                "group_d": {"b": "param4"},
            },
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
                "param3": {"module": "fixed", "value": 3.0},
                "param4": {"module": "fixed", "value": 4.0},
            },
            ["group_a", "group_b", "group_c", "group_d"],
            {
                "a": [("param1", "group_a"), ("param2", "group_b")],
                "b": [("param3", "group_c"), ("param4", "group_d")],
            },
        ),
        (
            {
                "group_a": {"a": "param1"},
                "group_b": {"a": "param2"},
                "group_c": {"b": "param3"},
                "group_d": {"b": "param4"},
            },
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
                "param3": {"module": "fixed", "value": 3.0},
                "param4": {"module": "fixed", "value": 4.0},
            },
            ["group_a", "group_b", "group_c"],
            {"a": [("param1", "group_a"), ("param2", "group_b")]},
        ),
    ],
)
def test_conflicting_parameter_renaming_value_error(
    groups: dict[IdentifierString, dict[IdentifierString, IdentifierString]],
    parameters: ModuleGroupModel,
    group_names: list[IdentifierString],
    conflicting_renames: dict[
        IdentifierString, list[tuple[IdentifierString, IdentifierString]]
    ],
) -> None:
    """Test that ValueError is raised for conflicting parameter renaming."""
    with pytest.raises(
        ValueError, match=r"^Parameter renaming conflicts detected:.*"
    ) as exc_info:
        ParameterCollection(parameters, groups, group_names)
    error_message = str(exc_info.value).splitlines()
    assert len(error_message) == len(conflicting_renames) + 1
    for rename_conflict, details in conflicting_renames.items():
        msg = f"  '{rename_conflict}' is mapped from: " + ", ".join([
            f"'{param}' from group '{source}'" for param, source in details
        ])
        assert msg in error_message


@pytest.mark.parametrize(
    ("groups", "parameters", "group_names", "final_mapping"),
    [
        (
            {},
            {"param1": {"module": "fixed", "value": 1.0}},
            [],
            {"param1": "param1"},
        ),
        (
            {"group1": {"renamed1": "param1"}},
            {"param1": {"module": "fixed", "value": 1.0}},
            ["group1"],
            {"renamed1": "param1"},
        ),
        (
            {"group1": {"renamed1": "param1"}},
            {"param1": {"module": "fixed", "value": 1.0}},
            [],
            {"param1": "param1"},
        ),
        (
            {"group1": {"renamed": "param1"}, "group2": {"renamed": "param2"}},
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
            },
            ["group1"],
            {"renamed": "param1"},
        ),
        (
            {"group1": {"renamed": "param1"}, "group2": {"renamed": "param2"}},
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
            },
            ["group2"],
            {"renamed": "param2"},
        ),
        (
            {"group1": {"renamed": "param1"}, "group2": {"renamed": "param2"}},
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
            },
            [],
            {"param1": "param1", "param2": "param2"},
        ),
        (
            {
                "group_a": {"a": "param1"},
                "group_b": {"a": "param2"},
                "group_y": {"b": "param3"},
                "group_z": {"b": "param4"},
            },
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
                "param3": {"module": "fixed", "value": 3.0},
                "param4": {"module": "fixed", "value": 4.0},
            },
            [],
            {
                "param1": "param1",
                "param2": "param2",
                "param3": "param3",
                "param4": "param4",
            },
        ),
        (
            {
                "group_a": {"a": "param1"},
                "group_b": {"a": "param2"},
                "group_y": {"b": "param3"},
                "group_z": {"b": "param4"},
            },
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
                "param3": {"module": "fixed", "value": 3.0},
                "param4": {"module": "fixed", "value": 4.0},
            },
            ["group_a", "group_y"],
            {
                "a": "param1",
                "b": "param3",
            },
        ),
        (
            {
                "group_a": {"a": "param1"},
                "group_b": {"a": "param2"},
                "group_y": {"b": "param3"},
                "group_z": {"b": "param4"},
            },
            {
                "param1": {"module": "fixed", "value": 1.0},
                "param2": {"module": "fixed", "value": 2.0},
                "param3": {"module": "fixed", "value": 3.0},
                "param4": {"module": "fixed", "value": 4.0},
            },
            ["group_b"],
            {
                "a": "param2",
                "param3": "param3",
                "param4": "param4",
            },
        ),
    ],
)
def test_final_mapping_attribute(
    groups: dict[IdentifierString, dict[IdentifierString, IdentifierString]],
    parameters: ModuleGroupModel,
    group_names: list[IdentifierString],
    final_mapping: dict[IdentifierString, IdentifierString],
) -> None:
    """Test that the final mapping attribute is correctly computed."""
    collection = ParameterCollection(parameters, groups, group_names)
    assert collection._final_mapping == final_mapping
