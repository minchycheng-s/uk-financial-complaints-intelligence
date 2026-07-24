import pandas as pd

from customer_harm.profiling.values import profile_values


def test_profiles_markers_without_replacing_them() -> None:
    series = pd.Series([10, 0, -2, None, " ", "-", "*", "N/A", "#VALUE!"], dtype="object")

    result = profile_values(series, "Complaints received", "number")

    assert result["semantic_type"] == "integer_like"
    assert result["null_count"] == 1
    assert result["whitespace_string_count"] == 1
    assert result["missing_marker_count"] == 1
    assert result["suppressed_marker_count"] == 1
    assert result["not_applicable_marker_count"] == 1
    assert result["excel_error_count"] == 1
    assert result["zero_count"] == 1
    assert result["negative_count"] == 1


def test_profiles_mixed_numeric_and_text_values() -> None:
    result = profile_values(pd.Series([1, "2", "unexpected"]), "Measure", "general")

    assert result["semantic_type"] == "mixed"
    assert result["numeric_parse_success_percent"] == 66.6667
    assert "unexpected" in result["non_numeric_examples"]


def test_identifier_and_percentage_semantics_use_business_context() -> None:
    assert profile_values(pd.Series([123456, 654321]), "FRN", "number")["semantic_type"] == "identifier"
    assert profile_values(pd.Series([0.25, 0.5]), "Percentage upheld", "percentage")["semantic_type"] == "percentage"
