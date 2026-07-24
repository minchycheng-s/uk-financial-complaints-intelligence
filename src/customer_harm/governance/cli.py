"""CLI for the management action and approval register."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.governance.actions import build_governance_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate management actions and build governance status reports."
    )
    parser.add_argument(
        "--register",
        type=Path,
        default=Path("data/mappings/management_action_register.csv"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/management_action_status.md"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("data/processed/governance/management_action_summary.json"),
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
    )
    try:
        summary = build_governance_report(args.register, args.report, args.summary)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error(
            "event=governance_report_aborted error=%s", exc
        )
        return 2
    logging.getLogger(__name__).info(
        "event=governance_report_complete summary=%s", summary
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
