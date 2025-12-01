"""A test module with a BaseModel class but no build function."""

from pydantic import BaseModel


class TestModel(BaseModel):
    """A test model for testing auto-generated build function."""

    name: str
    value: int
