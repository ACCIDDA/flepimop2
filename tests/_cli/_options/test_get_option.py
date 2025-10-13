"""Tests for the `get_option` function in `flepimop2._cli._options`."""

import pytest

from flepimop2._cli._options import COMMON_OPTIONS, get_option


@pytest.mark.parametrize("name", ["nope", "does not exist", "another fake option"])
def test_key_error_when_option_not_found(name: str) -> None:
    """Test that get_option raises KeyError for unknown option names."""
    assert name not in COMMON_OPTIONS
    with pytest.raises(
        KeyError, match=rf"^\"Unknown option '{name}'\. Available options:"
    ):
        get_option(name)
