"""Command-line entry point for reviewed FCA extraction."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from customer_harm.extraction.config import ExtractionConfig
from customer_harm.extraction.pipeline import extract_workbooks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract reviewed FCA firm-level workbooks.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw/fca/firm_level"))
    parser.add_argument("--profiling-dir", type=Path, default=Path("data/interim/profiling"))
    parser.add_argument("--mappings-dir", type=Path, default=Path("data/mappings"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/interim/extracted"))
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level,
                        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
    try:
        extract_workbooks(ExtractionConfig(args.input_dir, args.profiling_dir,
                                           args.mappings_dir, args.output_dir))
    except (FileNotFoundError, KeyError, ValueError) as exc:
        logging.getLogger(__name__).error("event=extraction_aborted error=%s", exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
