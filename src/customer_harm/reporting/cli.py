"""CLI for dashboard-ready reporting tables."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.reporting.pipeline import run_reporting_build


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build dashboard-ready reporting tables.")
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/reporting"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        summary = run_reporting_build(args.processed_dir, args.output_dir)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=reporting_build_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=reporting_build_complete summary=%s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
