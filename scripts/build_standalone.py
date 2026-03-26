#!/usr/bin/env python3
"""
Generate a standalone CLI script from print.py + lib/*.py.

Usage:
    python3 build_standalone.py
"""

from __future__ import annotations

import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "scripts/thermalprint.py"

MODULE_ORDER = [
    ROOT / "lib" / "config.py",
    ROOT / "lib" / "formatting.py",
    ROOT / "lib" / "inputs.py",
    ROOT / "lib" / "markdown_converter.py",
    ROOT / "lib" / "printer.py",
]

ENTRYPOINT_PATH = ROOT / "print.py"

UV_HEADER = """#!/usr/bin/env -S uv run --script
# This script generated from https://github.com/sadreck/ThermalMarky
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "python-escpos[all]",
#   "python-dotenv",
#   "platformdirs",
# ]
# ///
"""


def _strip_internal_imports(text: str) -> str:
    """Remove imports that only make sense in the modular layout."""
    output_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("from lib."):
            continue

        output_lines.append(line)

    return "\n".join(output_lines).rstrip() + "\n"


def _read_module_block(path: Path) -> str:
    original = path.read_text()
    transformed = _strip_internal_imports(original)
    return f"# --- begin: {path.relative_to(ROOT)} ---\n{transformed}# --- end: {path.relative_to(ROOT)} ---\n"


def _read_entrypoint_block(path: Path) -> str:
    text = _strip_internal_imports(path.read_text())
    return f"# --- begin: {path.relative_to(ROOT)} ---\n{text}# --- end: {path.relative_to(ROOT)} ---\n"


def build() -> str:
    parts: list[str] = [UV_HEADER, "\n"]

    for path in MODULE_ORDER:
        if not path.is_file():
            raise FileNotFoundError(f"Missing module: {path}")
        parts.append(_read_module_block(path))
        parts.append("\n")

    if not ENTRYPOINT_PATH.is_file():
        raise FileNotFoundError(f"Missing entrypoint: {ENTRYPOINT_PATH}")
    parts.append(_read_entrypoint_block(ENTRYPOINT_PATH))

    return "".join(parts).rstrip() + "\n"


def main() -> int:
    content = build()
    OUTPUT_PATH.write_text(content)
    OUTPUT_PATH.chmod(OUTPUT_PATH.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
