"""CLI for management action evidence."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.governance.action_evidence import build_action_evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build analytical evidence for management actions."
    )
    parser.add_argument(
        "--observations",
        type=Path,
        default=Path("data/processed/reporting/dashboard_firm_product_period.csv"),
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("data/processed/reporting/dashboard_warning_rule_detail.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/governance/action_evidence"),
    )
    parser.add_argument("--latest-period", default="2025-H2")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
    )
    try:
        summary = build_action_evidence(
            args.observations, args.rules, args.output_dir, args.latest_period
        )
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error(
            "event=action_evidence_aborted error=%s", exc
        )
        return 2
    logging.getLogger(__name__).info(
        "event=action_evidence_complete summary=%s", summary
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
