"""Command-line interface for FCA workbook profiling."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.profiling.pipeline import ProfileConfig, ProfilingRunError, profile_workbooks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Profile FCA firm-level complaint workbooks.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw/fca/firm_level"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/interim/profiling"))
    parser.add_argument("--metadata-dir", type=Path, default=Path("data/metadata"))
    parser.add_argument("--source-inventory", type=Path, default=Path("docs/source_inventory.csv"))
    parser.add_argument("--review-decisions", type=Path,
                        default=Path("data/mappings/profiling_review_decisions.csv"))
    parser.add_argument("--review-report", type=Path, default=Path("docs/profiling_review_report.md"))
    parser.add_argument("--extraction-readiness", type=Path,
                        default=Path("docs/extraction_readiness.md"))
    parser.add_argument("--header-scan-rows", type=int, default=40)
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        profile_workbooks(ProfileConfig(args.input_dir, args.output_dir, args.metadata_dir,
                                        args.header_scan_rows, source_inventory_path=args.source_inventory,
                                        review_decisions_path=args.review_decisions,
                                        review_report_path=args.review_report,
                                        extraction_readiness_path=args.extraction_readiness))
    except (FileNotFoundError, NotADirectoryError, ValueError, ProfilingRunError) as exc:
        logging.getLogger(__name__).error("event=profiling_aborted error=%s", exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
