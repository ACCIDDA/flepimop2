# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
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
