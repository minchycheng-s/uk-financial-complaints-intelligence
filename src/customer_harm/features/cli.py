"""CLI for analysis feature construction."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.features.pipeline import run_feature_build


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build firm/product trend and peer features.")
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/features"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        summary = run_feature_build(args.processed_dir, args.output_dir)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=feature_build_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=feature_build_complete summary=%s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
