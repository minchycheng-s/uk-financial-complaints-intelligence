"""CLI for Tableau presentation tables, manifest and preview."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.reporting.tableau_pack import run_tableau_pack


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Tableau dashboard delivery pack.")
    parser.add_argument("--reporting-dir", type=Path, default=Path("data/processed/reporting"))
    parser.add_argument("--tableau-dir", type=Path, default=Path("tableau"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        summary = run_tableau_pack(args.reporting_dir, args.tableau_dir)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=tableau_pack_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=tableau_pack_complete summary=%s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
