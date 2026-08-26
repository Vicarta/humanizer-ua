#!/usr/bin/env python3
"""Зібрати ZIP навички humanizer-ua для Claude/Codex."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


SKILL_REL = Path("skills") / "humanizer-ua"
BAD_NAMES = {".DS_Store", "__pycache__"}
BAD_SUFFIXES = {".pyc"}


def build_release_zip(repo_root: Path, output: Path) -> None:
    source = repo_root / SKILL_REL
    if not source.is_dir():
        raise FileNotFoundError(f"немає папки навички: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_dir():
                continue
            rel = path.relative_to(source.parent)
            if any(part in BAD_NAMES for part in rel.parts) or path.suffix in BAD_SUFFIXES:
                continue
            archive.write(path, rel.as_posix())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist/humanizer-ua.zip")
    parser.add_argument("repo_root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    try:
        build_release_zip(root, output)
    except OSError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"RELEASE_ZIP: {output}")
    print("RESULT: PASS build-release-zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

