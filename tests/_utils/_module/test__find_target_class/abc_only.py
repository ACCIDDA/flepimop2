"""A test module with a ProcessABC subclass but not BaseModel."""

from flepimop2.configuration import ConfigurationModel
from flepimop2.process.abc import ProcessABC


class TestProcess(ProcessABC):
    """A test process that inherits from ABC but not BaseModel."""

    def _process(self, *, configuration: ConfigurationModel, dry_run: bool) -> None:
        """Dummy process implementation."""
