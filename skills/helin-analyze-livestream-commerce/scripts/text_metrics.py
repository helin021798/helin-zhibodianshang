#!/usr/bin/env python3
"""Count effective speech units and estimate duration for transcript segments."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path


TOKEN_PATTERN = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]|[A-Za-z0-9]+(?:[._%+-][A-Za-z0-9]+)*"
)


def count_effective_units(text: str) -> int:
    """Count each CJK character and each contiguous Latin/digit token as one unit."""
    return len(TOKEN_PATTERN.findall(text))


def estimate_duration(units: int, chars_per_minute: float = 250.0) -> dict[str, object]:
    """Return machine-readable and report-friendly duration values."""
    if chars_per_minute <= 0:
        raise ValueError("chars_per_minute must be greater than zero")

    seconds = round(units / chars_per_minute * 60)
    rounded_minutes = math.floor(units / chars_per_minute + 0.5)
    if seconds < 60:
        display = "<1分钟"
    else:
        display = f"约{max(1, rounded_minutes)}分钟"

    hours, remainder = divmod(seconds, 3600)
    minutes, seconds_part = divmod(remainder, 60)
    timecode = f"{hours:02d}:{minutes:02d}:{seconds_part:02d}"

    return {
        "seconds": seconds,
        "timecode": timecode,
        "report_display": display,
    }


def analyze_file(path: Path, chars_per_minute: float) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: file must be UTF-8 or UTF-8 with BOM") from exc

    units = count_effective_units(text)
    return {
        "file": str(path),
        "effective_units": units,
        "chars_per_minute": chars_per_minute,
        "estimated_duration": estimate_duration(units, chars_per_minute),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Count effective Chinese speech units in one or more UTF-8 transcript "
            "segments and estimate duration."
        )
    )
    parser.add_argument("files", nargs="+", type=Path, help="UTF-8 transcript segment files")
    parser.add_argument(
        "--chars-per-minute",
        type=float,
        default=250.0,
        help="Speech-rate assumption; default: 250",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        results = [analyze_file(path, args.chars_per_minute) for path in args.files]
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
