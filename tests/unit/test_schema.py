import pytest
import pandas as pd

from customer_harm.profiling.schema import canonical_sheet_name, classify_sheet_type, compare_schemas


@pytest.mark.parametrize(
    ("sheet", "expected"),
    [
        ("Opened", "metric_wide_table"),
        ("Consumer Credit", "consumer_credit_metric_table"),
        ("Context - Provision", "context_rate_table"),
        ("Trading Names", "firm_alias_reference"),
        ("Main return Joint reporters", "joint_reporter_reference"),
        ("Notes", "product_reference"),
    ],
)
def test_real_sheet_variants_receive_structural_types(sheet: str, expected: str) -> None:
    assert classify_sheet_type(canonical_sheet_name(sheet)) == expected


def test_schema_rename_uses_position_and_semantic_evidence() -> None:
    sheets = pd.DataFrame([
        {"reporting_period": "2025-H1", "canonical_sheet": "opened", "sheet": "Opened", "header_row": 1},
        {"reporting_period": "2025-H2", "canonical_sheet": "opened", "sheet": "Opened", "header_row": 1},
    ])
    columns = pd.DataFrame([
        {"reporting_period": "2025-H1", "canonical_sheet": "opened", "normalised_column": "firm group",
         "column": "Firm Group", "storage_dtype": "string", "semantic_type": "identifier",
         "column_position": 2, "number_format_class": "general", "missing_percent": 0.0},
        {"reporting_period": "2025-H2", "canonical_sheet": "opened", "normalised_column": "group",
         "column": "Group", "storage_dtype": "string", "semantic_type": "identifier",
         "column_position": 2, "number_format_class": "general", "missing_percent": 0.0},
    ])

    result = compare_schemas(columns, sheets)

    assert result.change_type.tolist() == ["possible_column_renamed"]
    assert result.iloc[0].review_status == "manual_review"
    assert "position and semantic type" in result.iloc[0].evidence
