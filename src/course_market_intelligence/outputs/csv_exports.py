"""CSV exports for every dataset in a research run."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _write(rows: list[dict], path: Path) -> str:
    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    df.to_csv(path, index=False)
    return str(path)


def export_all(report: dict, out_dir: Path, slug: str) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    paths["competitors_csv"] = _write(
        report.get("competitors", []), out_dir / f"{slug}_competitors.csv"
    )
    paths["keywords_csv"] = _write(
        report.get("keywords", []), out_dir / f"{slug}_keywords.csv"
    )
    paths["seo_metrics_csv"] = _write(
        report.get("seo_metrics", []), out_dir / f"{slug}_seo_metrics.csv"
    )
    paths["trend_signals_csv"] = _write(
        report.get("trend_rows", []), out_dir / f"{slug}_trend_signals.csv"
    )
    paths["job_market_csv"] = _write(
        report.get("job_market_rows", []), out_dir / f"{slug}_job_market_signals.csv"
    )
    paths["gaps_csv"] = _write(
        report.get("gaps", []), out_dir / f"{slug}_gaps.csv"
    )
    paths["revenue_csv"] = _write(
        report.get("revenue_rows", []), out_dir / f"{slug}_revenue_model.csv"
    )
    paths["source_audit_csv"] = _write(
        report.get("source_audit", []), out_dir / f"{slug}_source_audit.csv"
    )
    return paths
