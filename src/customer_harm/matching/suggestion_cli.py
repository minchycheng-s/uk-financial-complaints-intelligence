"""CLI for manual-review firm match suggestions."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.matching.suggestions import run_suggestion_generation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Suggest possible FRN matches without accepting them.")
    parser.add_argument("--resolved-dir", type=Path, default=Path("data/interim/resolved"))
    parser.add_argument("--extracted-dir", type=Path, default=Path("data/interim/extracted"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/interim/resolved"))
    parser.add_argument("--decisions", type=Path,
                        default=Path("data/mappings/firm_match_review_decisions.csv"))
    parser.add_argument("--suggestions-per-firm", type=int, default=3)
    args = parser.parse_args(argv)
    if args.suggestions_per_firm < 1 or args.suggestions_per_firm > 10:
        parser.error("--suggestions-per-firm must be between 1 and 10")
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        summary = run_suggestion_generation(args.resolved_dir, args.extracted_dir,
                                            args.output_dir, args.decisions,
                                            args.suggestions_per_firm)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=firm_suggestions_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=firm_suggestions_complete summary=%s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
