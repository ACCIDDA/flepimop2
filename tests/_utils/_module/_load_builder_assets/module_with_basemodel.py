"""A test module with a BaseModel class but no build function."""

from pydantic import BaseModel

from flepimop2.module import ModuleABC


class TestModel(ModuleABC, BaseModel):
    """A test model for testing auto-generated build function."""

    module: str = "test_model"
    name: str
    value: int
