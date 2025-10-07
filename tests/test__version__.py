"""Unit tests for `flepimop2.__version__`."""

from flepimop2 import __version__


def test_version_is_string() -> None:
    """Test that `__version__` is a string."""
    assert isinstance(__version__, str)
