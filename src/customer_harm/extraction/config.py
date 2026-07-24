"""Configuration for the FCA extraction pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractionConfig:
    input_dir: Path = Path("data/raw/fca/firm_level")
    profiling_dir: Path = Path("data/interim/profiling")
    mappings_dir: Path = Path("data/mappings")
    output_dir: Path = Path("data/interim/extracted")

