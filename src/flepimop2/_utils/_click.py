from typing import TypeVar

from click import BadOptionUsage

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


def _get_config_target(group: dict[str, T], name: str | None) -> T:
    """
    Get a `T` by name from a group.

    Args:
        name: The name of the module target. If `None`, defaults to the first item
          in group.
        group: The module group to get the target from.

    Returns:
        The `T` with the specified name.

    Raises:
        click.BadOptionUsage: If the specified name is not found in the group.
    """
    if name is None:
        name = next(iter(group.keys()))
    res = group.get(name)
    if res is None:
        msg = f"Module target '{name}' not found in configuration."
        raise BadOptionUsage(option_name="target", message=msg)
    return res
