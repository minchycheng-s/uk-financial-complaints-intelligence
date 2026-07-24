"""CLI for comparing warning methodology versions."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.analytics.methodology_comparison import run_methodology_comparison


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare warning methodology versions.")
    parser.add_argument("--v1", type=Path,
                        default=Path("data/processed/warnings/firm_product_warning_summary.csv"))
    parser.add_argument("--v2", type=Path,
                        default=Path("data/processed/warnings_v2/firm_product_warning_summary.csv"))
    parser.add_argument("--reviews", type=Path,
                        default=Path("data/mappings/warning_case_review_decisions.csv"))
    parser.add_argument("--output-dir", type=Path,
                        default=Path("data/processed/warnings_comparison"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        summary = run_methodology_comparison(args.v1, args.v2, args.reviews, args.output_dir)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=methodology_comparison_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=methodology_comparison_complete summary=%s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
