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
# /// script
# requires-python = ">=3.11,<3.15"
# dependencies = [
#   "pyyaml>=6.0.3",
# ]
# ///
"""Generate citation documentation page from `CITATION.cff`."""

from collections.abc import Mapping
from pathlib import Path

import yaml


def doi_url(value: str) -> str:
    """
    Normalize a DOI string into a DOI URL.

    Args:
        value: The DOI value.

    Returns:
        The DOI URL.

    """
    return f"https://doi.org/{value.removeprefix('https://doi.org/')}"


def get_identifier_mappings(
    citation: dict[str, object],
) -> list[dict[str, object]]:
    """
    Extract identifier mappings from parsed CFF metadata.

    Args:
        citation: Parsed `CITATION.cff` content.

    Returns:
        Identifier entries as dictionaries.

    """
    identifiers = citation.get("identifiers")
    if not isinstance(identifiers, list):
        return []
    return [dict(entry) for entry in identifiers if isinstance(entry, Mapping)]


def get_zenodo_doi(citation: dict[str, object]) -> str | None:
    """
    Find the Zenodo DOI to advertise on the docs page.

    Args:
        citation: Parsed `CITATION.cff` content.

    Returns:
        The Zenodo DOI if available, otherwise `None`.

    """
    for identifier in get_identifier_mappings(citation):
        if str(identifier.get("type")) != "doi":
            continue
        if "zenodo" not in str(identifier.get("description", "")).lower():
            continue
        value = identifier.get("value")
        if value is not None:
            return str(value)
    doi = citation.get("doi")
    if doi is None:
        return None
    return str(doi)


def build_page_content(citation: dict[str, object]) -> list[str]:
    """
    Build the generated citation page.

    Args:
        citation: Parsed `CITATION.cff` content.

    Returns:
        Markdown lines for `docs/citation.md`.

    """
    repo_url = str(citation.get("repository-code") or citation.get("url") or "")
    source_url = f"{repo_url}/blob/main/CITATION.cff" if repo_url else ""
    content = ["# Citation", ""]

    if zenodo_doi := get_zenodo_doi(citation):
        zenodo_url = doi_url(zenodo_doi)
        content.extend(
            [
                f"Please cite `flepimop2` via Zenodo: [{zenodo_doi}]({zenodo_url}).",
                "",
            ],
        )
    else:
        content.extend(
            [
                "Citation metadata for `flepimop2` is maintained in `CITATION.cff`.",
                "",
            ],
        )

    if source_url:
        content.extend(
            [
                (
                    f"Additional repository citation metadata is "
                    f"stored in [`CITATION.cff`]({source_url})."
                ),
                "",
            ],
        )

    return content


def main() -> None:
    """Generate `docs/citation.md` from `CITATION.cff`."""
    root = Path(__file__).parent.parent
    citation = yaml.safe_load((root / "CITATION.cff").read_text())
    citation_md = root / "docs" / "citation.md"
    citation_md.write_text("\n".join(build_page_content(citation)))


if __name__ == "__main__":
    main()
