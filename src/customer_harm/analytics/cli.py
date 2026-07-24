"""CLI for building processed analysis-ready tables."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.analytics.tables import run_analysis_table_build


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build analysis-ready FCA fact and dimensions.")
    parser.add_argument("--input", type=Path,
                        default=Path("data/interim/resolved/complaint_metrics_resolved_reviewed.csv"))
    parser.add_argument("--quality-decisions", type=Path,
                        default=Path("data/mappings/metric_quality_decisions.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        summary = run_analysis_table_build(args.input, args.quality_decisions, args.output_dir)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=analysis_table_build_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=analysis_table_build_complete summary=%s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
