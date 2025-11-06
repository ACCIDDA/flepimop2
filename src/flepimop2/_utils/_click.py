from typing import TypeVar

from click import BadOptionUsage, UsageError

T = TypeVar("T")
U = TypeVar("U")


def _override_or_val(override: T | None, value: U) -> T | U:
    """
    Return the override value if it is not None, otherwise return the value.

    Args:
        override: Optional override value.
        value: The value to return if the override is None.

    Returns:
        The `override` value if it is not None, otherwise `value`.
    """
    return value if override is None else override


def _get_config_target(group: dict[str, T], name: str | None, group_name: str) -> T:
    """
    Get a `T` by name from a group.

    Args:
        group: The module group to get the target from.
        name: The name of the module target. If `None`, defaults to the first item
          in group.
        group_name: The name of the group, for error messages.

    Returns:
        The `T` with the specified name.

    Raises:
        click.UsageError: If the group is empty.
        click.BadOptionUsage: If the specified name is not found in the group.
    """
    if not group:
        msg = f"No targets available in the group for '{group_name}'."
        raise UsageError(msg)
    if name is None:
        name = next(iter(group.keys()))
    res = group.get(name)
    if res is None:
        msg = f"Target '{name}' not available from {group.keys()} for '{group_name}'."
        raise BadOptionUsage(option_name="target", message=msg)
    return res
