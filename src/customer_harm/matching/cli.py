"""CLI for conservative firm identity resolution."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.matching.resolution import run_firm_resolution


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve extracted FCA firm names to unique FRNs.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/interim/extracted"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/interim/resolved"))
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        summary = run_firm_resolution(args.input_dir, args.output_dir)
    except (FileNotFoundError, ValueError) as exc:
        logging.getLogger(__name__).error("event=firm_resolution_aborted error=%s", exc)
        return 2
    logging.getLogger(__name__).info("event=firm_resolution_complete summary=%s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
