"""Validate release readiness and create a GitHub release."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess  # noqa: S404
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, Literal
from zoneinfo import ZoneInfo

from pydantic import TypeAdapter

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
SEMVER_PATTERN: Final[re.Pattern[str]] = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
GH_RELEASE_LIST_TYPE: Final[TypeAdapter[list[dict[Literal["tagName"], str]]]] = (
    TypeAdapter(list[dict[Literal["tagName"], str]])
)


@dataclass(frozen=True, order=True)
class SemVer:
    """Semantic version container."""

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, raw: str) -> SemVer:
        """
        Parse a semantic version string.

        Args:
            raw: The semantic version string to parse.

        Returns:
            The parsed semantic version.

        Raises:
            ValueError: If `raw` is not a valid `X.Y.Z` semantic version string.
        """
        match = SEMVER_PATTERN.fullmatch(raw)
        if match is None:
            msg = f"Invalid semantic version: {raw!r}."
            raise ValueError(msg)
        major, minor, patch = (int(part) for part in match.groups())
        return cls(major=major, minor=minor, patch=patch)

    def __str__(self) -> str:
        """
        Format semantic version.

        Returns:
            The semantic version formatted as `X.Y.Z`.
        """
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_next_increment_from(self, previous: SemVer) -> bool:
        """Return whether this version is the next semantic increment."""
        is_patch = (
            self.major == previous.major
            and self.minor == previous.minor
            and self.patch == previous.patch + 1
        )
        is_minor = (
            self.major == previous.major
            and self.minor == previous.minor + 1
            and self.patch == 0
        )
        is_major = (
            self.major == previous.major + 1 and self.minor == 0 and self.patch == 0
        )
        return is_patch or is_minor or is_major


def get_gh_bin() -> str:
    """
    Resolve the GitHub CLI path or raise if unavailable.

    Returns:
        The path to the `gh` executable.

    Raises:
        FileNotFoundError: If `gh` is not available on `PATH`.
    """
    gh_bin = shutil.which("gh")
    if gh_bin is None:
        msg = "GitHub CLI (`gh`) not found on PATH."
        raise FileNotFoundError(msg)
    return gh_bin


def get_version() -> SemVer:
    """
    Read and validate the project version from pyproject.toml.

    Returns:
        The parsed project semantic version.
    """
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    return SemVer.parse(str(pyproject["project"]["version"]))


def collapse_bullet_lines(lines: list[str]) -> list[str]:
    """
    Collapse wrapped markdown bullet text to one line per bullet.

    Bullet indentation is preserved to maintain nesting levels.

    Args:
        lines: The raw changelog lines to normalize.

    Returns:
        The normalized lines with multi-line bullets collapsed.
    """
    collapsed: list[str] = []
    bullet_prefix: str | None = None
    bullet_parts: list[str] = []

    def flush_bullet() -> None:
        nonlocal bullet_prefix, bullet_parts
        if bullet_prefix is None:
            return
        joined = " ".join(part for part in bullet_parts if part).strip()
        collapsed.append(
            f"{bullet_prefix}{joined}" if joined else bullet_prefix.rstrip()
        )
        bullet_prefix = None
        bullet_parts = []

    for line in lines:
        bullet_match = re.match(r"^(?P<indent>\s*)-\s+(?P<text>.*)$", line)
        if bullet_match is not None:
            flush_bullet()
            bullet_prefix = f"{bullet_match.group('indent')}- "
            bullet_parts = [bullet_match.group("text").strip()]
            continue
        if bullet_prefix is None:
            collapsed.append(line)
            continue
        stripped = line.strip()
        if not stripped:
            flush_bullet()
            collapsed.append(line)
            continue
        bullet_parts.append(stripped)

    flush_bullet()
    return collapsed


def validate_and_extract_changelog_section(
    version: SemVer, *, create: bool = False
) -> str:
    """
    Validate changelog format and return release notes for the current version.

    Args:
        version: The release version expected at the top of the changelog.
        create: Whether the caller is creating a release instead of doing a dry run.

    Returns:
        The validated release notes body for the current version.

    Raises:
        ValueError: If the changelog headings, date, or release notes are invalid.
    """
    changelog_lines = (REPO_ROOT / "CHANGELOG.md").read_text().splitlines()

    h2_headings = [line for line in changelog_lines if line.startswith("## ")]
    if not h2_headings:
        msg = "CHANGELOG.md must contain at least one level-2 release heading."
        raise ValueError(msg)

    if any(h.lower() == "## [unreleased]" for h in h2_headings):
        msg = "CHANGELOG.md must not contain a `## [Unreleased]` heading."
        raise ValueError(msg)

    today = datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    expected_heading = f"## [{version}] - {today}"
    if h2_headings[0] != expected_heading:
        msg = (
            "Top CHANGELOG.md heading must match current version and today's date: "
            f"`{expected_heading}`."
        )
        raise ValueError(msg)

    header_idx = changelog_lines.index(expected_heading)
    section_lines: list[str] = []
    for line in changelog_lines[header_idx + 1 :]:
        if line.startswith("## "):
            break
        stripped = line.strip()
        if stripped.startswith("-") and re.search(r"[A-Za-z0-9]", stripped) is None:
            msg = f"Invalid changelog bullet point: {line!r}."
            raise ValueError(msg)
        section_lines.append(line)
    notes = "\n".join(collapse_bullet_lines(section_lines)).strip()
    if not notes:
        msg = f"CHANGELOG section for {version} is empty."
        raise ValueError(msg)
    if not create:
        sys.stdout.write(
            f"Extracted release notes for version {version}:\n\n{notes}\n\n"
        )

    return notes


def validate_release_state(version: SemVer) -> None:
    """
    Validate version state against existing GitHub releases.

    Args:
        version: The version being prepared for release.

    Raises:
        ValueError: If the version already exists or is not the next increment.
    """
    proc = subprocess.run(  # noqa: S603
        [
            get_gh_bin(),
            "release",
            "list",
            "--json",
            "tagName",
            "--limit",
            "1",
            "--order",
            "desc",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    releases = GH_RELEASE_LIST_TYPE.validate_json(proc.stdout)
    if not releases:
        return
    latest_tag = str(releases[0]["tagName"])
    latest_version_raw = latest_tag.removeprefix("v")
    latest_version = SemVer.parse(latest_version_raw)
    if version == latest_version:
        msg = f"Version {version} already exists as a GitHub release ({latest_tag})."
        raise ValueError(msg)
    if not version.is_next_increment_from(latest_version):
        msg = (
            "Current version must be the next semantic increment from the latest "
            f"release. current={version}, latest={latest_version}."
        )
        raise ValueError(msg)


def create_release(version: SemVer, notes: str, *, create: bool = False) -> None:
    """Create GitHub release using gh CLI."""
    tag = f"v{version}"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".md",
        prefix="flepimop2-release-notes-",
        delete=False,
    ) as temp_file:
        temp_file.write(notes)
        temp_file.close()
        command = [
            get_gh_bin(),
            "release",
            "create",
            tag,
            "--title",
            tag,
            "--notes-file",
            temp_file.name,
        ]
        if version.major == 0:
            command.append("--prerelease")
        if create:
            subprocess.run(command, check=True)  # noqa: S603
            return
        sys.stdout.write(f"Dry run of GitHub release command: {' '.join(command)}")


def main() -> None:
    """Run release checks and optionally create the release."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create the GitHub release after all checks pass.",
    )
    args = parser.parse_args()

    version = get_version()
    validate_release_state(version)
    notes = validate_and_extract_changelog_section(version, create=args.create)
    create_release(version, notes, create=args.create)


if __name__ == "__main__":
    main()
