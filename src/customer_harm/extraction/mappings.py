"""Load and validate human-reviewed extraction mappings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


def normalise_label(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


def base_product_label(header: str) -> str:
    """Remove a parenthesised measurement qualifier without losing the raw header."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", str(header)).strip()


@dataclass(frozen=True)
class MappingRegistry:
    products: dict[str, str]
    sheets: pd.DataFrame
    exceptions: pd.DataFrame

    @classmethod
    def load(cls, directory: Path) -> "MappingRegistry":
        required = {
            "product_group_mappings.csv": {"raw_label", "canonical_product_group"},
            "sheet_mappings.csv": {"canonical_sheet", "output_entity", "metric_name", "measurement_unit"},
            "reviewed_exceptions.csv": {"reporting_period", "canonical_sheet", "raw_field", "rule", "review_item_id"},
        }
        frames = {}
        for filename, columns in required.items():
            path = directory / filename
            if not path.exists():
                raise FileNotFoundError(f"Required extraction mapping does not exist: {path}")
            frame = pd.read_csv(path, dtype=str).fillna("")
            missing = columns - set(frame.columns)
            if missing:
                raise ValueError(f"{filename} is missing columns: {sorted(missing)}")
            frames[filename] = frame
        product_frame = frames["product_group_mappings.csv"]
        if product_frame.raw_label.map(normalise_label).duplicated().any():
            raise ValueError("Product mapping contains duplicate normalised raw labels.")
        products = dict(zip(product_frame.raw_label.map(normalise_label),
                            product_frame.canonical_product_group))
        sheets = frames["sheet_mappings.csv"]
        if sheets.canonical_sheet.duplicated().any():
            raise ValueError("Sheet mapping contains duplicate canonical sheets.")
        return cls(products, sheets.set_index("canonical_sheet"),
                   frames["reviewed_exceptions.csv"])

    def product_group(self, raw_header: str) -> str | None:
        return self.products.get(normalise_label(base_product_label(raw_header)))

    def sheet(self, canonical_sheet: str) -> dict[str, str]:
        if canonical_sheet not in self.sheets.index:
            raise KeyError(f"No mapping for canonical sheet: {canonical_sheet}")
        return self.sheets.loc[canonical_sheet].to_dict()

