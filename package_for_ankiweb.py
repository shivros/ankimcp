"""Package the AnkiMCP add-on into an .ankiaddon archive suitable for AnkiWeb.

The produced .ankiaddon file matches the structure described in the AnkiWeb
sharing documentation:
https://addon-docs.ankiweb.net/sharing.html
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
from pathlib import Path
from typing import Iterable
from zipfile import ZIP_DEFLATED, ZipFile

DEFAULT_SOURCE = Path("src") / "ankimcp"
EXCLUDE_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".pyd", ".so", ".dylib"}
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an .ankiaddon package ready for uploading to AnkiWeb."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Path to the add-on source directory (defaults to src/ankimcp).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Exact path of the output .ankiaddon file. If omitted, a file will "
        "be created in ./dist/ using the add-on package name.",
    )
    parser.add_argument(
        "--version",
        type=str,
        help="Optional version string to include in the generated filename.",
    )
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="Omit the timestamp from the generated filename when --output is not provided.",
    )
    return parser.parse_args()


def load_manifest(source: Path) -> dict:
    manifest_path = source / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"manifest.json not found in {source}. AnkiWeb packages require a manifest."
        )
    with manifest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_output_path(
    requested_output: Path | None,
    package_name: str,
    version: str | None,
    include_timestamp: bool,
) -> Path:
    if requested_output is not None:
        output_path = requested_output
        if output_path.suffix != ".ankiaddon":
            output_path = output_path.with_suffix(".ankiaddon")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    dist_dir = Path("dist")
    dist_dir.mkdir(parents=True, exist_ok=True)

    safe_package = re.sub(r"[^A-Za-z0-9_.-]", "_", package_name)
    name_parts: list[str] = [safe_package]

    if version:
        safe_version = re.sub(r"[^A-Za-z0-9_.-]", "_", version)
        if safe_version:
            name_parts.append(safe_version)

    if include_timestamp:
        timestamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        name_parts.append(timestamp)

    filename = "-".join(name_parts) + ".ankiaddon"
    return dist_dir / filename


def iter_source_files(source: Path) -> Iterable[Path]:
    for path in sorted(source.rglob("*")):
        if should_exclude(path):
            continue
        if path.is_file():
            yield path


def should_exclude(path: Path) -> bool:
    if any(part in EXCLUDE_PARTS for part in path.parts):
        return True
    if path.name in EXCLUDE_NAMES:
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return False


def create_archive(source: Path, destination: Path) -> None:
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for file_path in iter_source_files(source):
            archive.write(file_path, file_path.relative_to(source))


def main() -> None:
    args = parse_args()
    source = args.source.resolve()

    if not source.exists() or not source.is_dir():
        raise NotADirectoryError(f"Source directory {source} does not exist or is not a directory.")

    manifest = load_manifest(source)
    package_name = manifest.get("package") or manifest.get("name") or source.name

    output_path = build_output_path(
        requested_output=args.output,
        package_name=package_name,
        version=args.version,
        include_timestamp=not args.no_timestamp,
    )

    create_archive(source, output_path)

    print(f"Packaged add-on from {source} -> {output_path}")


if __name__ == "__main__":
    main()
