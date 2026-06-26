"""JSON report writer."""

from __future__ import annotations

import json
from pathlib import Path


def write_json(report: dict, out_dir: Path, slug: str) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{slug}_report.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    return str(path)
