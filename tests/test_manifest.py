"""Tests for the manifest requirements."""

import json
from pathlib import Path

from homeassistant.util.package import parse_requirement_safe

MANIFEST = json.loads((Path(__file__).parents[1] / "manifest.json").read_text())


def test_requirements_pin_a_version_home_assistant_can_check() -> None:
    """Home Assistant reinstalls a requirement on every start if it cannot check its version.

    It cannot for direct URL requirements (`name @ url`), but it can for the legacy
    `url#name==version` form.
    """
    for requirement in MANIFEST["requirements"]:
        parsed = parse_requirement_safe(requirement)
        assert parsed is not None
        assert parsed.url is None
        assert str(parsed.specifier).startswith("==")
