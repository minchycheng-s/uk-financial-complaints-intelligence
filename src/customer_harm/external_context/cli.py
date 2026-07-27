"""Command-line interface for external-context integration."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from customer_harm.external_context.pipeline import run_external_context_build


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build BOE/ONS context and FOS taxonomy mapping candidates."
    )
    parser.add_argument("--config", type=Path, default=Path("config/external_context.json"))
    parser.add_argument(
        "--boe-input", type=Path,
        default=Path("data/raw/boe/Bank Rate history and data  Bank of England Database.csv"),
    )
    parser.add_argument("--ons-input", type=Path, default=Path("data/raw/ons/mm23.csv"))
    parser.add_argument(
        "--fos-input", type=Path,
        default=Path("data/raw/fos/our-taxonomy-full-product-list.xlsx"),
    )
    parser.add_argument(
        "--interim-dir", type=Path, default=Path("data/interim/external_context")
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/processed/external_context")
    )
    parser.add_argument(
        "--mapping-path", type=Path,
        default=Path("data/mappings/fca_fos_product_mapping.csv"),
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
    )
    try:
        summary = run_external_context_build(
            args.config, args.boe_input, args.ons_input, args.fos_input,
            args.interim_dir, args.output_dir, args.mapping_path,
        )
    except (FileNotFoundError, ValueError, KeyError, json.JSONDecodeError) as exc:
        logging.getLogger(__name__).error(
            "event=external_context_build_aborted error=%s", exc
        )
        return 2
    logging.getLogger(__name__).info(
        "event=external_context_build_complete summary=%s", summary
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
