#!/usr/bin/env python3
"""Статичні інваріанти пакета humanizer-ua."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "humanizer-ua" / "SKILL.md"
CATALOG = ROOT / "skills" / "humanizer-ua" / "references" / "catalog.md"
EXPECTED_PATTERNS = 46
EXPECTED_HARD_RULES = 20


def main() -> int:
    errors: list[str] = []
    skill_text = SKILL.read_text(encoding="utf-8")
    catalog_text = CATALOG.read_text(encoding="utf-8")

    if not skill_text.startswith("---\n") or "\nname: humanizer-ua\n" not in skill_text:
        errors.append("некоректний frontmatter або name")
    description = re.search(r'^description:\s*"([^"]+)"$', skill_text, re.MULTILINE)
    if not description:
        errors.append("description має бути в подвійних лапках і в одному рядку")
    elif len(description.group(1)) > 1024:
        errors.append("description перевищує 1024 символи")
    if "scripts/scan.py" not in skill_text or "references/catalog.md" not in skill_text:
        errors.append("SKILL.md не маршрутизує до сканера або каталогу")

    found = [int(value) for value in re.findall(r"^\*\*(\d+)\.", catalog_text, re.MULTILINE)]
    if found != list(range(1, EXPECTED_PATTERNS + 1)):
        errors.append(f"нумерація каталогу не суцільна 1..{EXPECTED_PATTERNS}: {found}")

    sys.path.insert(0, str(SKILL.parent / "scripts"))
    import scan  # noqa: PLC0415

    if len(scan.HARD_RULES) != EXPECTED_HARD_RULES:
        errors.append(f"сильних правил {len(scan.HARD_RULES)}, очікувалося {EXPECTED_HARD_RULES}")
    if scan.VERSION != "1.0.4" or "v1.0.4" not in skill_text:
        errors.append("версії skill і scanner не збігаються")

    for manifest in (
        ROOT / ".claude-plugin" / "plugin.json",
        ROOT / ".claude-plugin" / "marketplace.json",
        ROOT / ".codex-plugin" / "plugin.json",
    ):
        try:
            json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"некоректний JSON {manifest.relative_to(ROOT)}: {exc}")

    for path in SKILL.parent.rglob("*"):
        if not path.name.isascii():
            errors.append(f"не-ASCII шлях у пакеті навички: {path.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print("RESULT: FAIL lint-skill")
        return 1
    print(f"✓ каталог: {EXPECTED_PATTERNS} патерни")
    print(f"✓ сильні маркери: {EXPECTED_HARD_RULES}")
    print("✓ manifests і frontmatter валідні")
    print("RESULT: PASS lint-skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

