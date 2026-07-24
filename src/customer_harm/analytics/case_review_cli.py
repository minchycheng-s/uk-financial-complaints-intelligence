"""CLI for validating and summarising warning case reviews."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.analytics.case_review import run_case_review


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate sampled warning-case decisions.")
    parser.add_argument("--sample", type=Path,
                        default=Path("data/processed/warnings/validation/warning_review_sample.csv"))
    parser.add_argument("--decisions", type=Path,
                        default=Path("data/mappings/warning_case_review_decisions.csv"))
    parser.add_argument("--output-dir", type=Path,
                        default=Path("data/processed/warnings/validation"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        summary = run_case_review(args.sample, args.decisions, args.output_dir)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=warning_case_review_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=warning_case_review_complete summary=%s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
