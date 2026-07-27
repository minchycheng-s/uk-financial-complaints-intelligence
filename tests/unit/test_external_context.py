from pathlib import Path

import pandas as pd
from openpyxl import Workbook

from customer_harm.external_context.pipeline import (
    build_boe_half_year_context,
    build_fca_fos_mapping_template,
    build_fos_taxonomy,
    build_ons_context,
    period_bounds,
    periods_between,
    reporting_period,
    validate_outputs,
)


def test_reporting_period_helpers() -> None:
    assert reporting_period(pd.Timestamp("2025-06-30")) == "2025-H1"
    assert reporting_period(pd.Timestamp("2025-07-01")) == "2025-H2"
    assert period_bounds("2025-H2")[1] == pd.Timestamp("2025-12-31")
    assert periods_between("2024-H2", "2025-H2") == ["2024-H2", "2025-H1", "2025-H2"]


def test_boe_context_uses_effective_rate_at_period_boundaries() -> None:
    source = pd.DataFrame({
        "Date Changed": ["16 Dec 21", "05 Aug 21", "19 Mar 20"],
        "Rate": [0.25, 0.10, 0.10],
    })
    result = build_boe_half_year_context(source, ["2021-H1", "2021-H2"])
    first, second = result.iloc[0], result.iloc[1]
    assert first.start_bank_rate == first.end_bank_rate == 0.10
    assert second.start_bank_rate == 0.10
    assert second.end_bank_rate == 0.25
    assert second.rate_decision_count == 2


def test_ons_context_selects_only_configured_series_and_aggregates() -> None:
    source = pd.DataFrame({
        "Title": ["2025 JAN", "2025 FEB", "2025 JUL", "2025 AUG"],
        "CPI": [3.0, 4.0, 5.0, 6.0],
        "Insurance": [8.0, 10.0, 12.0, 14.0],
        "Unused": [999, 999, 999, 999],
    })
    config = {
        "cpi": {"source_column": "CPI", "unit": "percentage_points", "decision_use": "general"},
        "insurance": {
            "source_column": "Insurance", "unit": "percentage_points",
            "decision_use": "insurance",
        },
    }
    monthly, half_year = build_ons_context(source, config, ["2025-H1", "2025-H2"])
    assert len(monthly) == 8
    row = half_year[
        half_year.reporting_period.eq("2025-H1") & half_year.indicator_name.eq("cpi")
    ].iloc[0]
    assert row.period_mean == 3.5
    assert row.period_end_value == 4.0
    assert row.within_period_change == 1.0


def _write_fos_workbook(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Banking and Credit"
    sheet.append([None, "Old taxonomy", None, None, None, "New taxonomy", None, None])
    sheet.append([None, "Sector", "Product group", "Product type",
                  None, "Sector", "Product group", "Product type"])
    sheet.append([None, "Old", "Old group", "Old type",
                  None, "Banking and Payments", "Banking Services", "Current Accounts"])
    sheet.append([None, None, None, None, None, None, None, "Savings Accounts"])
    insurance = workbook.create_sheet("Insurance")
    insurance.append([None, "Old taxonomy", None, None, None, "New taxonomy", None, None])
    insurance.append([None, "Sector", "Product group", "Product type",
                      None, "Sector", "Product group", "Product type"])
    insurance.append([None, "Old", "Old group", "Old type",
                      None, "Insurance", "Property Insurance", "Buildings Insurance"])
    workbook.save(path)


def test_fos_taxonomy_is_tidy_and_mapping_suggestions_remain_pending(tmp_path: Path) -> None:
    path = tmp_path / "fos.xlsx"
    _write_fos_workbook(path)
    taxonomy = build_fos_taxonomy(path)
    savings = taxonomy[
        taxonomy.taxonomy_version.eq("new") & taxonomy.fos_product_type.eq("Savings Accounts")
    ].iloc[0]
    assert savings.fos_sector == "Banking and Payments"
    assert savings.fos_product_group == "Banking Services"
    mappings = build_fca_fos_mapping_template(taxonomy)
    assert set(mappings.review_decision) == {"pending_review"}
    assert mappings.approved_fca_product_group.eq("").all()
    assert "banking_and_credit_cards" in set(mappings.suggested_fca_product_group)


def test_validation_accepts_complete_synthetic_outputs(tmp_path: Path) -> None:
    boe = pd.DataFrame({
        "reporting_period": ["2025-H1"],
        "start_bank_rate": [4.5], "end_bank_rate": [4.25],
        "minimum_bank_rate": [4.25], "maximum_bank_rate": [4.5],
    })
    monthly = pd.DataFrame({
        "observation_date": ["2025-01-01"], "indicator_name": ["cpi"]
    })
    half_year = pd.DataFrame({
        "reporting_period": ["2025-H1"], "indicator_name": ["cpi"]
    })
    taxonomy = pd.DataFrame({"fos_product_type": ["Current Accounts"]})
    mappings = pd.DataFrame({
        "mapping_id": ["FOS-1"],
        "suggested_fca_product_group": ["banking_and_credit_cards"],
        "review_decision": ["pending_review"],
    })
    assert validate_outputs(
        boe, monthly, half_year, taxonomy, mappings, ["2025-H1"], 1
    ) == []
