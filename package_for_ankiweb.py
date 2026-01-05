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
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator
from zipfile import ZIP_DEFLATED, ZipFile

DEFAULT_SOURCE = Path("src") / "ankimcp"
EXCLUDE_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
# Note: .so/.dylib/.pyd are KEPT for native extensions (pydantic_core, etc.)
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db"}
RUNTIME_DEPENDENCIES = ["mcp>=1.9.4"]

# Platform mappings for pip wheel downloads
PLATFORM_TAGS = {
    "linux": "manylinux2014_x86_64",
    "macos": "macosx_10_9_x86_64",
    "macos-arm": "macosx_11_0_arm64",
    "windows": "win_amd64",
}


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
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip bundling runtime dependencies (useful if the source already includes them).",
    )
    parser.add_argument(
        "--python-version",
        type=str,
        default="3.13",
        help="Target Python version for vendored dependencies (default: 3.13 for Anki 25.x).",
    )
    parser.add_argument(
        "--platform",
        type=str,
        choices=list(PLATFORM_TAGS.keys()),
        default="linux",
        help="Target platform for vendored dependencies (default: linux).",
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


def copy_source_tree(source: Path, destination: Path) -> Path:
    target = destination / source.name
    shutil.copytree(source, target)
    return target


def vendor_dependencies(
    target_dir: Path,
    packages: Iterable[str],
    python_version: str = "3.11",
    platform: str = "linux",
) -> None:
    """Download and vendor dependencies as platform-specific wheels.

    This properly handles native extensions like pydantic_core by downloading
    pre-compiled wheels for the target platform.
    """
    pip_platform = PLATFORM_TAGS.get(platform, PLATFORM_TAGS["linux"])

    with tempfile.TemporaryDirectory() as download_dir:
        download_path = Path(download_dir)

        # Download wheels for the target platform
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--dest",
            str(download_path),
            "--only-binary",
            ":all:",
            "--python-version",
            python_version,
            "--platform",
            pip_platform,
            *packages,
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            # Fallback: try without platform restriction (for pure Python packages)
            cmd = [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--dest",
                str(download_path),
                *packages,
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(
                    f"Failed to download dependencies: {exc.stderr or exc.stdout}"
                ) from exc

        # Extract wheels into target directory
        target_dir.mkdir(parents=True, exist_ok=True)

        for wheel in download_path.glob("*.whl"):
            # Skip anki/aqt packages (provided by Anki itself)
            package_name = wheel.name.split("-")[0].lower()
            if package_name in {"anki", "aqt"}:
                continue

            shutil.unpack_archive(wheel, target_dir, "zip")

        # Keep .dist-info directories - they're needed for importlib.metadata
        # (packages like mcp use this to read their version)

        # Clean up __pycache__ directories
        for pycache in target_dir.rglob("__pycache__"):
            shutil.rmtree(pycache)


@contextmanager
def build_staging_source(
    source: Path,
    include_dependencies: bool = True,
    python_version: str = "3.11",
    platform: str = "linux",
) -> Iterator[Path]:
    """Yield a temporary copy of the source with optional vendored dependencies."""
    with tempfile.TemporaryDirectory() as temp_dir:
        staging_root = Path(temp_dir)
        staging_source = copy_source_tree(source, staging_root)

        if include_dependencies:
            vendor_dir = staging_source / "vendor"
            vendor_dependencies(
                vendor_dir,
                RUNTIME_DEPENDENCIES,
                python_version=python_version,
                platform=platform,
            )

        yield staging_source


def main() -> None:
    args = parse_args()
    source = args.source.resolve()

    if not source.exists() or not source.is_dir():
        raise NotADirectoryError(
            f"Source directory {source} does not exist or is not a directory."
        )

    manifest = load_manifest(source)
    package_name = manifest.get("package") or manifest.get("name") or source.name

    output_path = build_output_path(
        requested_output=args.output,
        package_name=package_name,
        version=args.version,
        include_timestamp=not args.no_timestamp,
    )

    with build_staging_source(
        source=source,
        include_dependencies=not args.skip_deps,
        python_version=args.python_version,
        platform=args.platform,
    ) as staging_source:
        create_archive(staging_source, output_path)

    deps_info = ""
    if args.skip_deps:
        deps_info = " (skipped vendored deps)"
    else:
        deps_info = f" (vendored for Python {args.python_version} on {args.platform})"

    print(f"Packaged add-on from {source} -> {output_path}{deps_info}")


if __name__ == "__main__":
    main()
