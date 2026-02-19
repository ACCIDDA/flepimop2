# /// script
# requires-python = ">=3.11,<3.15"
# ///
"""Generate authors and maintainers documentation page for flepimop2."""

import tomllib
from pathlib import Path


def format_person(person: dict[str, str]) -> str | None:
    """
    Format a person dictionary into a string.

    Args:
        person: A dictionary containing the person's information.

    Returns:
        A formatted string with the person's name and optional contact information, or
        `None` if the name is missing.

    """
    if (entry := person.get("name")) is None:
        return None
    if email := person.get("email"):
        entry += f" [:material-email:](mailto:{email})"
    if github := person.get("github"):
        entry += f" [:simple-github:](https://github.com/{github})"
    if orcid := person.get("orcid"):
        entry += f" [:simple-orcid:](https://orcid.org/{orcid})"
    return f"- {entry}"


def main() -> None:
    """Generate `authors.md` from `pyproject.toml` data."""
    root = Path(__file__).parent.parent

    pyproject = tomllib.loads((root / "pyproject.toml").read_text())

    authors = pyproject.get("project", {}).get("authors", [])
    maintainers = pyproject.get("project", {}).get("maintainers", [])
    people = pyproject.get("tool", {}).get("flepimop2", {}).get("people", [])

    people_by_email = {
        person["email"]: person for person in people if "email" in person
    }

    authors = [a | people_by_email.get(a.get("email"), {}) for a in authors]
    maintainers = [m | people_by_email.get(m.get("email"), {}) for m in maintainers]

    content = ["---", "hide:", "  - 'toc'", "---", "", "# Authors and Maintainers", ""]
    if formatted_authors := [p for a in authors if (p := format_person(a)) is not None]:
        content.extend(["## Authors", "", *formatted_authors, ""])
    if formatted_maintainers := [
        p for m in maintainers if (p := format_person(m)) is not None
    ]:
        content.extend(["## Maintainers", "", *formatted_maintainers, ""])

    authors_md = root / "docs" / "authors.md"
    if authors_md.exists():
        authors_md.unlink()
    authors_md.write_text("\n".join(content))


if __name__ == "__main__":
    main()
