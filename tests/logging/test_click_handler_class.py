"""Unit tests for the `ClickHandler` class in `flepimop2._cli._logging` module."""

import io
import logging

import pytest

from flepimop2._cli._logging import _PUNCTUATION, ClickHandler


@pytest.mark.parametrize(
    "msg",
    [
        "This is a message",
        "Another message.",
        "Start to a list:",
        "Middle of a sentence,",
        "Oh-no!",
        "Question?",
    ],
)
@pytest.mark.parametrize("punctuate", [True, False])
def test_click_handler_punctuation_formatting(msg: str, *, punctuate: bool) -> None:
    """Test `ClickHandler` message punctuation formatting."""
    buffer = io.StringIO()
    handler = ClickHandler(level=logging.DEBUG, file=buffer, punctuate=punctuate)
    log_record = logging.LogRecord(
        name="",
        level=logging.DEBUG,
        pathname="",
        lineno=1,
        msg=msg,
        args=None,
        exc_info=None,
    )
    handler.emit(log_record)
    buffer.seek(0)
    handler_msg = buffer.getvalue()
    if not punctuate:
        assert handler_msg == msg + "\n"
    else:
        assert handler_msg == (msg if msg.endswith(_PUNCTUATION) else f"{msg}.") + "\n"
