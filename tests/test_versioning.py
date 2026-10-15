"""Test version management and bump logic."""

import json
import os
import sys
from pathlib import Path

# Add script directory to sys.path
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", ".github", "scripts")
    ),
)

from bump_version import bump_version


def test_manifest_version_parity():
    """Verify manifest.json version is valid and present."""
    root = Path(__file__).resolve().parent.parent
    manifest_path = root / "custom_components" / "omniroute" / "manifest.json"
    assert manifest_path.exists()
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)
    assert "version" in data
    assert data["domain"] == "omniroute"


def test_bump_logic():
    """Test SemVer and beta bump logic."""
    scenarios = [
        (None, "patch", "stable", [], "1.0.0"),
        (None, "minor", "beta", [], "1.0.0-beta.0"),
        ("1.0.0", "patch", "stable", ["v1.0.0"], "1.0.1"),
        ("1.0.0", "minor", "stable", ["v1.0.0"], "1.1.0"),
        ("1.0.0", "major", "stable", ["v1.0.0"], "2.0.0"),
        ("1.0.0", "patch", "beta", ["v1.0.0"], "1.0.1-beta.0"),
        ("1.0.1-beta.0", "patch", "beta", ["v1.0.1-beta.0", "v1.0.0"], "1.0.1-beta.1"),
        ("1.0.1-beta.1", "patch", "stable", ["v1.0.1-beta.1", "v1.0.0"], "1.0.1"),
        ("1.0.1-beta.1", "minor", "beta", ["v1.0.1-beta.1", "v1.0.0"], "1.1.0-beta.0"),
        ("1.1.0-beta.0", "minor", "stable", ["v1.1.0-beta.0", "v1.0.0"], "1.1.0"),
    ]

    for current, bump, status, tags, expected in scenarios:
        result = bump_version(current, bump, status, all_tags=tags)
        assert result == expected, (
            f"Expected {expected} for ({current}, {bump}, {status}), got {result}"
        )
