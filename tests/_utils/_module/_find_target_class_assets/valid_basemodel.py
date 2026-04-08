"""A test module with a valid BaseModel subclass."""

from pydantic import BaseModel

from flepimop2.module import ModuleABC


class TestModel(ModuleABC, BaseModel):
    """A test model for testing _find_target_class."""

    module: str = "test_model"
    name: str
    value: int
