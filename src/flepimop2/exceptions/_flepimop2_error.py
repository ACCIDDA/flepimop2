from typing import Any


class Flepimop2Error(Exception):
    """
    Base class for exceptions provided by `flepimop2`.

    This class serves as the root for all custom exceptions in the `flepimop2` library.
    """

    __module__ = "flepimop2.exceptions"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.__module__ = "flepimop2.exceptions"
