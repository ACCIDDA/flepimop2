"""Unit tests for the `IdentifierString` type."""

import pytest
from pydantic import BaseModel, ValidationError

from flepimop2.configuration import IdentifierString


class Example(BaseModel):
    """Example model using IdentifierString."""

    name: IdentifierString


@pytest.mark.parametrize(
    "name",
    [
        "gamma",
        "valid_name",
        "valid_name_123",
        "r0",
    ],
)
def test_valid_identifier_strings(name: str) -> None:
    """Test that valid identifier strings are accepted."""
    example = Example(name=name)
    assert example.name == name


@pytest.mark.parametrize(
    "name",
    [
        "1invalidStart",
        "invalid char!",
        "-invalidStartHyphen",
        "invalidEnd-",
        "",
        "invalid@char",
        "A",
        "name-with-hyphens",
        "validName",
        "class",
        "def",
    ],
)
def test_invalid_identifier_strings(name: str) -> None:
    """Test that invalid identifier strings raise ValidationError."""
    with pytest.raises(ValidationError):
        Example(name=name)
