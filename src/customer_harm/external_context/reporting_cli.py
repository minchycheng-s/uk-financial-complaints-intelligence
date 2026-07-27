"""CLI for Tableau-ready external-context reporting tables."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.external_context.reporting import run_external_context_reporting


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build Tableau-ready BOE/ONS and product-period context tables."
    )
    parser.add_argument(
        "--external-context-dir", type=Path,
        default=Path("data/processed/external_context"),
    )
    parser.add_argument(
        "--reporting-dir", type=Path, default=Path("data/processed/reporting")
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
    )
    try:
        summary = run_external_context_reporting(
            args.external_context_dir, args.reporting_dir
        )
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error(
            "event=external_context_reporting_aborted error=%s", exc
        )
        return 2
    logging.getLogger(__name__).info(
        "event=external_context_reporting_complete summary=%s", summary
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
