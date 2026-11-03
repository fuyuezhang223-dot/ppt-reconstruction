#!/usr/bin/env python3
"""Create a reproducible GitHub ZIP with correct UTF-8 entry names."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".swp"}


def included_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES or path.name == ".DS_Store":
            continue
        if rel.parts[0] == "outputs" and rel.as_posix() != "outputs/.gitkeep":
            continue
        if path.name == "PACKAGE_FILES_SHA256.json":
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def write_hash_manifest(files: list[Path]) -> Path:
    rows = {}
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        rows[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    target = ROOT / "PACKAGE_FILES_SHA256.json"
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT.parent / "PPT_Reconstruction_Skill_v1.0.0_GitHub_Release.zip")
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    files = included_files()
    write_hash_manifest(files)
    files = included_files() + [ROOT / "PACKAGE_FILES_SHA256.json"]

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            rel = path.relative_to(ROOT).as_posix()
            archive.write(path, arcname=f"ppt-reconstruction/{rel}")

    with zipfile.ZipFile(output, "r") as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC check failed at {bad}")
        bad_names = [name for name in archive.namelist() if "σ" in name or "╕" in name]
        if bad_names:
            raise RuntimeError("ZIP contains suspicious mojibake paths")
        non_ascii = [info for info in archive.infolist() if any(ord(ch) > 127 for ch in info.filename)]
        invalid_utf8_flags = [info.filename for info in non_ascii if not (info.flag_bits & 0x800)]
        if invalid_utf8_flags:
            raise RuntimeError(f"UTF-8 filename flag missing: {invalid_utf8_flags[:3]}")

    print(f"Release ZIP created: {output}")
    print(f"Files: {len(files)} | Size: {output.stat().st_size / (1024 * 1024):.1f} MiB")
    print("ZIP CRC and UTF-8 filename checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
