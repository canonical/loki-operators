#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Verify that the lokitool and loki OCI image major.minor versions match."""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COORDINATOR_CHARMCRAFT = REPO_ROOT / "coordinator" / "charmcraft.yaml"
WORKER_CHARMCRAFT = REPO_ROOT / "worker" / "charmcraft.yaml"

LOKITOOL_URL_RE = re.compile(
    r"grafana/loki/releases/download/v(\d+\.\d+)\.\d+/lokitool"
)
RENOVATE_TAG_RE = re.compile(r"tag:\s*(\d+\.\d+)")


def get_lokitool_version() -> str:
    """Extract lokitool major.minor version from the coordinator charmcraft.yaml."""
    content = COORDINATOR_CHARMCRAFT.read_text()
    match = LOKITOOL_URL_RE.search(content)
    if not match:
        sys.exit(
            f"ERROR: Could not extract lokitool version from {COORDINATOR_CHARMCRAFT}"
        )
    return match.group(1)


def get_loki_image_version() -> str:
    """Extract loki OCI image major.minor version from the worker charmcraft.yaml.

    Finds the upstream-source line within the loki-image resource block
    and extracts the version from the renovate comment tag.
    """
    in_loki_image = False
    loki_image_indent = -1

    for line in WORKER_CHARMCRAFT.read_text().splitlines():
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if stripped.startswith("loki-image:"):
            in_loki_image = True
            loki_image_indent = indent
            continue

        if in_loki_image:
            # Left the block when we hit a non-empty line at same or lesser indent.
            if stripped and indent <= loki_image_indent:
                break

            if "upstream-source:" in stripped:
                match = RENOVATE_TAG_RE.search(line)
                if match:
                    return match.group(1)

    sys.exit(
        f"ERROR: Could not extract loki image version from {WORKER_CHARMCRAFT}"
    )


def main():
    lokitool_version = get_lokitool_version()
    loki_image_version = get_loki_image_version()

    if lokitool_version != loki_image_version:
        sys.exit(
            f"ERROR: Version mismatch!\n"
            f"  lokitool version (coordinator/charmcraft.yaml): {lokitool_version}\n"
            f"  loki image tag   (worker/charmcraft.yaml):      {loki_image_version}\n"
            f"  These major.minor versions must match."
        )

    print(f"OK: lokitool and loki image versions match ({lokitool_version})")


if __name__ == "__main__":
    main()
