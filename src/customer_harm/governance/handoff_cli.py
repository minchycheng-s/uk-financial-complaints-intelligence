"""CLI for the business-review handoff and operational release gate."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.governance.handoff import build_business_review_handoff


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the business review handoff.")
    parser.add_argument("--register", type=Path, default=Path("data/mappings/management_action_register.csv"))
    parser.add_argument("--report", type=Path, default=Path("docs/business_review_handoff.md"))
    parser.add_argument("--gate", type=Path, default=Path("data/processed/governance/operational_release_gate.json"))
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
    )
    try:
        gate = build_business_review_handoff(args.register, args.report, args.gate)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=handoff_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=handoff_complete gate=%s", gate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
