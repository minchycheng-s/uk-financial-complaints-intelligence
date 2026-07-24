"""CLI for persistent-case investigation evidence packs."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.governance.persistent_cases import build_persistent_case_pack


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build persistent priority-case investigation packs."
    )
    parser.add_argument(
        "--observations",
        type=Path,
        default=Path(
            "data/processed/reporting/dashboard_firm_product_period.csv"
        ),
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("data/processed/reporting/dashboard_warning_rule_detail.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/governance/persistent_cases"),
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        default=Path("data/mappings/persistent_case_review_decisions.csv"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/persistent_case_review_status.md"),
    )
    parser.add_argument("--latest-period", default="2025-H2")
    parser.add_argument("--case-count", type=int, default=6)
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
    )
    try:
        summary = build_persistent_case_pack(
            args.observations,
            args.rules,
            args.output_dir,
            args.decisions,
            args.report,
            args.latest_period,
            args.case_count,
        )
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error(
            "event=persistent_case_pack_aborted error=%s", exc
        )
        return 2
    logging.getLogger(__name__).info(
        "event=persistent_case_pack_complete summary=%s", summary
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
