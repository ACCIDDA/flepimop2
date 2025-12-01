"""A test module with a valid BaseModel subclass."""

from pydantic import BaseModel


class TestModel(BaseModel):
    """A test model for testing _find_target_class."""

    name: str
    value: int
