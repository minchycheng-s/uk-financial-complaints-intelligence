from pathlib import Path

import pytest

from customer_harm.profiling.discovery import discover_workbooks, parse_reporting_period


def test_discover_workbooks_recursively_and_in_order(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "b.XLSX").touch()
    (tmp_path / "a.xlsx").touch()
    (tmp_path / "ignored.csv").touch()

    assert [path.name for path in discover_workbooks(tmp_path)] == ["a.xlsx", "b.XLSX"]


@pytest.mark.parametrize(
    ("filename", "expected"),
    [("fca_2021_h1.xlsx", "2021-H1"), ("firm-level-complaints-data-2025-h2.xlsx", "2025-H2")],
)
def test_parse_reporting_period(filename: str, expected: str) -> None:
    assert parse_reporting_period(filename) == expected


def test_parse_reporting_period_rejects_unknown_name() -> None:
    with pytest.raises(ValueError, match="Could not parse"):
        parse_reporting_period("complaints.xlsx")

