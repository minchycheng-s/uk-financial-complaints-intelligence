"""CLI for warning-methodology sensitivity analysis and review sampling."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.analytics.validation import run_methodology_validation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate warning methodology and create review samples.")
    parser.add_argument("--features", type=Path,
                        default=Path("data/processed/features/firm_product_period_features.csv"))
    parser.add_argument("--methodology", type=Path, default=Path("config/warning_methodology.json"))
    parser.add_argument("--output-dir", type=Path,
                        default=Path("data/processed/warnings/validation"))
    parser.add_argument("--sample-per-band", type=int, default=5)
    args = parser.parse_args(argv)
    if args.sample_per_band < 1:
        parser.error("--sample-per-band must be positive")
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        summary = run_methodology_validation(args.features, args.methodology,
                                             args.output_dir, args.sample_per_band)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=methodology_validation_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=methodology_validation_complete summary=%s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
