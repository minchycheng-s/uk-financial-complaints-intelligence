import pandas as pd

from customer_harm.profiling.definitions import (
    build_product_group_inventory,
    compare_definitions,
    compare_taxonomies,
    extract_notes_content,
    normalise_product_group,
)


def test_extract_notes_preserves_raw_group_and_adds_review_inheritance() -> None:
    matrix = [
        ["Notes on data tables", None],
        ["A sufficiently long narrative explaining the publication and its reporting basis " * 2, None],
        ["Product group", "Product/service name"],
        ["Banking and credit cards", "Credit cards"],
        [None, "Current accounts"],
        ["Decumulation & pensions (a)", "Annuities"],
        ["(a) Decumulation means converting pension assets into retirement income.", None],
    ]

    taxonomy, definitions = extract_notes_content(
        matrix, 2, {"workbook": "source.xlsx", "reporting_period": "2025-H1", "sheet": "Notes"}
    )

    assert taxonomy[1]["raw_product_group"] is None
    assert taxonomy[1]["inherited_product_group"] == "banking and credit cards"
    assert taxonomy[1]["group_was_inherited"] is True
    assert taxonomy[2]["footnote_marker"] == "a"
    assert any(record["definition_type"] == "footnote" for record in definitions)


def test_product_group_normalisation_separates_measurement_and_footnote() -> None:
    group, measurement, footnote = normalise_product_group(
        "Decumulation & pensions (per 1,000 policies in force)"
    )
    assert group == "decumulation & pensions"
    assert measurement == "per 1,000 policies in force"
    assert footnote is None


def test_product_inventory_classifies_total_and_unexpected_header() -> None:
    columns = pd.DataFrame([
        {"workbook": "a.xlsx", "reporting_period": "2025-H1", "sheet": "Opened",
         "canonical_sheet": "opened", "sheet_type": "metric_wide_table", "column_position": 5,
         "column": "Banking and credit cards"},
        {"workbook": "a.xlsx", "reporting_period": "2025-H1", "sheet": "Opened",
         "canonical_sheet": "opened", "sheet_type": "metric_wide_table", "column_position": 6,
         "column": "Grand Total"},
        {"workbook": "a.xlsx", "reporting_period": "2025-H1", "sheet": "Opened",
         "canonical_sheet": "opened", "sheet_type": "metric_wide_table", "column_position": 7,
         "column": "unnamed_7"},
    ])

    result = build_product_group_inventory(columns)

    assert result.label_type.tolist() == ["product_group", "total", "unexpected_blank_header"]


def test_missing_notes_periods_are_explicit_in_comparisons() -> None:
    taxonomy = pd.DataFrame(columns=["reporting_period", "normalised_product_service_name",
                                     "inherited_product_group"])
    definitions = pd.DataFrame(columns=["reporting_period", "definition_key",
                                        "definition_text", "definition_text_hash"])

    taxonomy_result = compare_taxonomies(taxonomy, {"2025-H1"}, ("2025-H1", "2025-H2"))
    definition_result = compare_definitions(definitions, {"2025-H1"}, ("2025-H1", "2025-H2"))

    assert taxonomy_result.iloc[0].change_type == "product_reference_unavailable"
    assert definition_result.iloc[0].change_type == "definition_reference_unavailable"
