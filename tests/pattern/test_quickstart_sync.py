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
"""Guard that the copy pattern's template matches the documented quickstart."""

from pathlib import Path

from flepimop2.pattern.copy import _TEMPLATE_DIR

_QUICKSTART = Path(__file__).parents[2] / "docs" / "assets" / "quickstart-project"


def test_copy_template_matches_docs_quickstart() -> None:
    """
    Every documented quickstart file has a byte-identical copy in the template.

    `flepimop2 pattern` scaffolds `_TEMPLATE_DIR`, and the docs present
    `docs/assets/quickstart-project` as the project it produces. This fails if
    the packaged template and the documented quickstart drift apart.
    """
    files = sorted(
        path
        for path in _QUICKSTART.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    assert files, "no quickstart files found; did the docs path move?"
    for source in files:
        relative = source.relative_to(_QUICKSTART)
        target = _TEMPLATE_DIR / relative
        assert target.is_file(), f"template is missing {relative}"
        assert target.read_bytes() == source.read_bytes(), f"{relative} drifted"
