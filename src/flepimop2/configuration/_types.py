__all__ = []

from typing import Annotated

from pydantic import AfterValidator, Field

from flepimop2._utils._pydantic import _identifier_string

IdentifierString = Annotated[
    str,
    Field(min_length=1, max_length=255, pattern=r"^[a-z]([a-z0-9\_]*[a-z0-9])?$"),
    AfterValidator(_identifier_string),
]
"""A string type representing a valid identifier for named configuration elements."""
