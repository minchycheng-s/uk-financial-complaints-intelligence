"""Apply explicit human/agent-reviewed firm match decisions."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.matching.suggestions import run_review_application


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply reviewed firm match decisions safely.")
    parser.add_argument("--resolved-dir", type=Path, default=Path("data/interim/resolved"))
    parser.add_argument("--extracted-dir", type=Path, default=Path("data/interim/extracted"))
    parser.add_argument("--decisions", type=Path,
                        default=Path("data/mappings/firm_match_review_decisions.csv"))
    parser.add_argument("--identity-overrides", type=Path,
                        default=Path("data/mappings/firm_identity_overrides.csv"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        summary = run_review_application(args.resolved_dir, args.extracted_dir, args.decisions,
                                         args.identity_overrides)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=firm_review_application_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=firm_review_application_complete summary=%s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
