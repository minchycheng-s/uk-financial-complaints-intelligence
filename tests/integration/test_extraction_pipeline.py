import json
from pathlib import Path

import openpyxl
import pandas as pd

from customer_harm.extraction import ExtractionConfig, extract_workbooks


def test_extracts_a_wide_metric_sheet_to_long_records(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    profiling = tmp_path / "profiling"
    output = tmp_path / "output"
    raw.mkdir()
    profiling.mkdir()
    workbook_path = raw / "firm-level-complaints-data-2025-h2.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Opened"
    sheet.append(["Firm Name", "Group", "Joint Reporting", "Reporting period",
                  "Home finance", "Grand Total"])
    sheet.append(["Example Firm", "Example Group", "No", "2025-H2", 12, 12])
    workbook.save(workbook_path)
    pd.DataFrame([{
        "reporting_period": "2025-H2", "sheet": "Opened", "canonical_sheet": "opened",
        "header_row": 1, "last_value_row": 2, "last_value_column": 6,
    }]).to_csv(profiling / "sheet_inventory.csv", index=False)
    (profiling / "profiling_review_gate.json").write_text(json.dumps({
        "extraction_authorised": True, "profiling_review_status": "approved"
    }), encoding="utf-8")

    frames = extract_workbooks(ExtractionConfig(raw, profiling, Path("data/mappings"), output))

    metrics = frames["complaint_metrics"]
    assert list(metrics.product_group) == ["home_finance", "grand_total"]
    assert list(metrics.metric_value) == [12.0, 12.0]
    assert set(metrics.measurement_unit) == {"count"}
    assert frames["sheet_reconciliation"].iloc[0].reconciliation_status == "matched"
    assert frames["total_reconciliation"].iloc[0].reconciliation_status == "matched"
    assert (output / "extraction_summary.json").exists()
