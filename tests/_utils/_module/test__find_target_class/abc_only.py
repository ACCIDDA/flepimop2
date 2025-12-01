"""A test module with a ProcessABC subclass but not BaseModel."""

from flepimop2.process.abc import ProcessABC


class TestProcess(ProcessABC):
    """A test process that inherits from ABC but not BaseModel."""

    def _process(self, *, dry_run: bool) -> None:
        """Dummy process implementation."""
