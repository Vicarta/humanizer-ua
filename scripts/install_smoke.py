#!/usr/bin/env python3
"""Перевірити встановлювану поверхню навички й release ZIP."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from build_release_zip import build_release_zip


SKILL_REL = Path("skills") / "humanizer-ua"
REQUIRED = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/catalog.md",
    "scripts/scan.py",
)


def run_scanner(scanner: Path, text: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(scanner), "-", "--json"],
        input=text,
        text=True,
        capture_output=True,
        check=False,
    )


def validate_skill(skill: Path) -> list[str]:
    errors = [f"немає файла: {rel}" for rel in REQUIRED if not (skill / rel).is_file()]
    if errors:
        return errors
    clean = run_scanner(skill / "scripts" / "scan.py", "Ми перевірили звіт двічі. Помилку знайшли у другій таблиці.")
    if clean.returncode != 0:
        errors.append(f"чистий текст: exit {clean.returncode}: {clean.stderr}")
    else:
        try:
            payload = json.loads(clean.stdout)
        except json.JSONDecodeError as exc:
            errors.append(f"сканер повернув не JSON: {exc}")
        else:
            if payload.get("hard_ban_count") != 0 or "score" not in payload:
                errors.append("неправильна схема JSON для чистого тексту")
    banned = run_scanner(skill / "scripts" / "scan.py", "У сучасному світі цей сервіс є потужним інструментом.")
    if banned.returncode != 1:
        errors.append(f"текст із маркером: exit {banned.returncode}, очікувався 1")
    return errors


def validate_zip(path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
    for rel in REQUIRED:
        expected = f"humanizer-ua/{rel}"
        if expected not in names:
            errors.append(f"ZIP не містить {expected}")
    for name in names:
        if not name.startswith("humanizer-ua/"):
            errors.append(f"неочікуваний шлях у ZIP: {name}")
        if "__pycache__" in Path(name).parts or name.endswith(".pyc"):
            errors.append(f"службовий файл у ZIP: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".")
    parser.add_argument("--zip", dest="zip_path")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    source = root / SKILL_REL
    if not source.is_dir():
        print(f"ERROR: немає {source}")
        return 2

    with tempfile.TemporaryDirectory(prefix="humanizer-ua-smoke-") as tmp:
        installed = Path(tmp) / "skills" / "humanizer-ua"
        shutil.copytree(source, installed, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        zip_path = Path(args.zip_path).resolve() if args.zip_path else Path(tmp) / "humanizer-ua.zip"
        if not args.zip_path:
            build_release_zip(root, zip_path)
        errors = validate_skill(installed) + validate_zip(zip_path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print("RESULT: FAIL install-smoke")
        return 1
    print("RESULT: PASS install-smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

