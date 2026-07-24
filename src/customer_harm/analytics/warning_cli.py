"""CLI for explainable complaint early-warning indicators."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.analytics.warnings import run_warning_build


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build explainable early-warning indicators.")
    parser.add_argument("--features", type=Path,
                        default=Path("data/processed/features/firm_product_period_features.csv"))
    parser.add_argument("--methodology", type=Path,
                        default=Path("config/warning_methodology.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/warnings"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        summary = run_warning_build(args.features, args.methodology, args.output_dir)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=warning_build_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=warning_build_complete summary=%s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
