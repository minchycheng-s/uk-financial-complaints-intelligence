"""CLI for structured review of all v2 priority observations."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.analytics.priority_review import run_priority_review


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review all warning priority observations.")
    parser.add_argument("--summary", type=Path,
                        default=Path("data/processed/warnings_v2/firm_product_warning_summary.csv"))
    parser.add_argument("--indicators", type=Path,
                        default=Path("data/processed/warnings_v2/warning_indicators.csv"))
    parser.add_argument("--features", type=Path,
                        default=Path("data/processed/features/firm_product_period_features.csv"))
    parser.add_argument("--previous-reviews", type=Path,
                        default=Path("data/mappings/warning_case_review_decisions.csv"))
    parser.add_argument("--source-resolutions", type=Path,
                        default=Path("data/mappings/warning_v2_source_check_resolutions.csv"))
    parser.add_argument("--output", type=Path,
                        default=Path("data/mappings/warning_v2_priority_review_decisions.csv"))
    parser.add_argument("--summary-output", type=Path,
                        default=Path("data/processed/warnings_v2/validation/priority_review_summary.json"))
    parser.add_argument("--reviewer", default="Codex")
    parser.add_argument("--reviewed-at", default="2026-07-20")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        result = run_priority_review(
            args.summary, args.indicators, args.features, args.previous_reviews,
            args.output, args.summary_output, args.reviewer, args.reviewed_at,
            args.source_resolutions,
        )
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=priority_review_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=priority_review_complete summary=%s", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
