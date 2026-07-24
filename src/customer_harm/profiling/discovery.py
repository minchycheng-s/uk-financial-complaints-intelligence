"""Raw workbook discovery and source identity helpers."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

SUPPORTED_SUFFIXES = {".xlsx", ".xlsm"}
PERIOD_PATTERN = re.compile(r"(?P<year>20\d{2})[-_ ]?h(?P<half>[12])", re.IGNORECASE)


def discover_workbooks(input_dir: Path) -> list[Path]:
    """Discover supported workbooks recursively in deterministic order."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Raw workbook directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Raw workbook path is not a directory: {input_dir}")
    return sorted(
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.casefold() in SUPPORTED_SUFFIXES
    )


def parse_reporting_period(filename: str) -> str:
    """Parse and standardise a half-year period embedded in a filename."""
    match = PERIOD_PATTERN.search(Path(filename).name)
    if not match:
        raise ValueError(f"Could not parse reporting period from filename: {filename}")
    return f"{match.group('year')}-H{match.group('half')}"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Calculate a source-file checksum without loading the entire file."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()

