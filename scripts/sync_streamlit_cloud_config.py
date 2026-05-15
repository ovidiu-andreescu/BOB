#!/usr/bin/env python3
"""Sync or validate the Streamlit Cloud compatibility config."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "infra" / "streamlit" / "streamlit_config.toml"
TARGET = ROOT / ".streamlit" / "config.toml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="copy the canonical config")
    mode.add_argument("--check", action="store_true", help="validate the mirrored config")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not SOURCE.exists():
        print(f"Missing canonical Streamlit config: {SOURCE}", file=sys.stderr)
        return 1

    source_text = SOURCE.read_text(encoding="utf-8")

    if args.write:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(source_text, encoding="utf-8")
        print(f"Synced {TARGET.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)}")
        return 0

    if not TARGET.exists():
        print(f"Missing mirrored Streamlit config: {TARGET}", file=sys.stderr)
        return 1

    target_text = TARGET.read_text(encoding="utf-8")
    if target_text != source_text:
        print(
            f"{TARGET.relative_to(ROOT)} does not match {SOURCE.relative_to(ROOT)}. "
            "Run `make sync-cloud-config`.",
            file=sys.stderr,
        )
        return 1

    print("Streamlit Cloud config mirror is up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
