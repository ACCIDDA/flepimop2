# Copyright (C) 2026 Joshua Macdonald
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the provider-role schematic, or check its committed source/export identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess  # noqa: S404 -- invokes only fixed local documentation tools
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = hashlib.sha256(
        (HERE / "figure.tex").read_bytes() + Path(__file__).read_bytes()
    ).hexdigest()
    manifest = HERE / "manifest.json"
    if args.check:
        recorded = json.loads(manifest.read_text())
        if recorded["source_sha256"] != source or any(
            _digest(HERE / name) != value for name, value in recorded["exports"].items()
        ):
            msg = (
                "Regenerate the provider-role figure with "
                "docs/assets/provider-roles/build.py"
            )
            raise ValueError(msg)
        return
    latex = shutil.which("pdflatex")
    converter = shutil.which("pdftocairo")
    if latex is None or converter is None:
        msg = "Figure regeneration requires pdflatex and pdftocairo on PATH"
        raise RuntimeError(msg)
    with tempfile.TemporaryDirectory(prefix="provider-roles-") as directory:
        work = Path(directory)
        env = os.environ.copy()
        env["SOURCE_DATE_EPOCH"] = "946684800"
        env["FORCE_SOURCE_DATE"] = "1"
        subprocess.run(  # noqa: S603 -- fixed tool and repository-owned TeX; shell escape is disabled
            [
                latex,
                "-no-shell-escape",
                "-halt-on-error",
                "-interaction=nonstopmode",
                str(HERE / "figure.tex"),
            ],
            cwd=work,
            env=env,
            check=True,
            capture_output=True,
        )
        log = (work / "figure.log").read_text()
        if any(
            warning in log
            for warning in ["Overfull \\hbox", "Overfull \\vbox", "Missing character:"]
        ):
            msg = "Resolve the provider figure's TeX layout/glyph warnings"
            raise ValueError(msg)
        subprocess.run(  # noqa: S603 -- fixed converter and locally generated PDF
            [converter, "-svg", str(work / "figure.pdf"), str(work / "figure.svg")],
            check=True,
            capture_output=True,
        )
        for name in ["figure.pdf", "figure.svg"]:
            shutil.copyfile(work / name, HERE / name)
    svg_path = HERE / "figure.svg"
    svg = svg_path.read_text().replace(
        "<svg ", '<svg role="img" aria-labelledby="title description" ', 1
    )
    start = svg.index(">", svg.index("<svg ")) + 1
    annotation = (
        '<title id="title">Provider roles in a simulation</title>'
        '<desc id="description">Parameters supply values, systems bind model changes, '
        "engines advance state and backends persist results. Job and process providers "
        "supply distinct command-launch and task-execution roles.</desc>"
        '<rect width="100%" height="100%" fill="white"/>'
    )
    svg_path.write_text(svg[:start] + annotation + svg[start:])
    manifest.write_text(
        json.dumps(
            {
                "source_sha256": source,
                "exports": {
                    name: _digest(HERE / name) for name in ["figure.svg", "figure.pdf"]
                },
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    _main()
