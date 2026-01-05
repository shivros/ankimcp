#!/usr/bin/env python3
"""
Vendor dependencies for AnkiMCP addon.

This script downloads mcp and its dependencies (including pydantic with native extensions)
into the vendor/ directory for bundling with the Anki addon.

Usage:
    python scripts/vendor_dependencies.py [--python-version 3.11] [--platform linux]

Platforms: linux, macos, windows
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Dependencies to vendor (mcp will pull in pydantic, etc.)
DEPENDENCIES = [
    "mcp>=1.9.4",
]

# Packages to exclude (provided by Anki or not needed)
EXCLUDE_PACKAGES = [
    "anki",
    "aqt",
]


def get_pip_platform(platform_name: str) -> str:
    """Convert platform name to pip platform tag."""
    platforms = {
        "linux": "manylinux2014_x86_64",
        "macos": "macosx_10_9_x86_64",
        "macos-arm": "macosx_11_0_arm64",
        "windows": "win_amd64",
    }
    return platforms.get(platform_name, platforms["linux"])


def detect_platform() -> str:
    """Detect current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        if machine == "arm64":
            return "macos-arm"
        return "macos"
    elif system == "windows":
        return "windows"
    return "linux"


def vendor_dependencies(
    vendor_dir: Path,
    python_version: str = "3.11",
    platform_name: str | None = None,
) -> None:
    """Download and vendor dependencies."""

    if platform_name is None:
        platform_name = detect_platform()

    pip_platform = get_pip_platform(platform_name)

    print(f"Vendoring dependencies for Python {python_version} on {platform_name}")
    print(f"Target directory: {vendor_dir}")

    # Clean existing vendor directory
    if vendor_dir.exists():
        print("Cleaning existing vendor directory...")
        shutil.rmtree(vendor_dir)

    vendor_dir.mkdir(parents=True, exist_ok=True)

    # Download wheels
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--dest",
        str(vendor_dir),
        "--only-binary",
        ":all:",
        "--python-version",
        python_version,
        "--platform",
        pip_platform,
        *DEPENDENCIES,
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error downloading wheels:\n{result.stderr}")
        # Try without platform restriction for pure Python packages
        print("\nRetrying with mixed approach (wheels + source)...")
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--dest",
            str(vendor_dir),
            *DEPENDENCIES,
        ]
        subprocess.run(cmd, check=True)

    # Extract wheels
    print("\nExtracting wheels...")
    for wheel in vendor_dir.glob("*.whl"):
        # Skip excluded packages
        package_name = wheel.name.split("-")[0].lower()
        if package_name in [p.lower() for p in EXCLUDE_PACKAGES]:
            print(f"  Skipping {wheel.name} (excluded)")
            wheel.unlink()
            continue

        print(f"  Extracting {wheel.name}")
        shutil.unpack_archive(wheel, vendor_dir, "zip")
        wheel.unlink()

    # Remove .dist-info directories (not needed at runtime)
    for dist_info in vendor_dir.glob("*.dist-info"):
        shutil.rmtree(dist_info)

    # Remove __pycache__ directories
    for pycache in vendor_dir.rglob("__pycache__"):
        shutil.rmtree(pycache)

    print(f"\nVendored packages in {vendor_dir}:")
    for item in sorted(vendor_dir.iterdir()):
        if item.is_dir():
            print(f"  {item.name}/")


def main():
    parser = argparse.ArgumentParser(description="Vendor dependencies for AnkiMCP")
    parser.add_argument(
        "--python-version",
        default="3.11",
        help="Target Python version (default: 3.11)",
    )
    parser.add_argument(
        "--platform",
        choices=["linux", "macos", "macos-arm", "windows"],
        help="Target platform (default: auto-detect)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / "src" / "ankimcp" / "vendor",
        help="Output directory for vendored packages",
    )

    args = parser.parse_args()

    vendor_dependencies(
        vendor_dir=args.output,
        python_version=args.python_version,
        platform_name=args.platform,
    )

    print("\nDone! Remember to test the addon in Anki.")


if __name__ == "__main__":
    main()
