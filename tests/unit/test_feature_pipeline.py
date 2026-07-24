import pandas as pd

from customer_harm.features.pipeline import build_feature_tables, parse_source_window, validate_feature_tables


def test_source_window_supports_both_observed_date_formats() -> None:
    assert str(parse_source_window("01-01-2021 to 30-06-2021")[1].date()) == "2021-06-30"
    assert str(parse_source_window("2021-07-01 to 2021-12-31")[1].date()) == "2021-12-31"


def test_features_keep_measurements_separate_and_calculate_trend() -> None:
    rows = []
    for period, window, opened, upheld in [
        ("2025-H1", "2025-01-01 to 2025-06-30", 10, 0.2),
        ("2025-H2", "2025-07-01 to 2025-12-31", 15, 0.3),
    ]:
        common = {"firm_key": "FRN:123", "reporting_period": period,
                  "source_reporting_period": window, "product_group": "home_finance",
                  "is_analysis_ready_value": True, "is_product_level": True}
        rows.extend([
            {**common, "canonical_sheet": "opened", "metric_name": "complaints_opened",
             "measurement_unit": "count", "metric_value": opened},
            {**common, "canonical_sheet": "percentage_upheld", "metric_name": "complaints_upheld",
             "measurement_unit": "percentage", "metric_value": upheld},
        ])
    firms = pd.DataFrame([{"firm_key": "FRN:123", "resolved_frn": "123",
                           "display_firm_name": "Example", "identity_match_status": "matched",
                           "identity_match_confidence": "high"}])
    tables = build_feature_tables(pd.DataFrame(rows), firms)
    features = tables["firm_product_period_features"].sort_values("observation_end")
    assert list(features.complaints_opened_count) == [10, 15]
    assert list(features.complaints_upheld_pct) == [0.2, 0.3]
    assert features.iloc[1].change_complaints_opened_count == 5
    assert features.iloc[1].pct_change_complaints_opened_count == 0.5
    assert validate_feature_tables(tables, 4) == []


def test_zero_previous_value_does_not_create_infinite_growth() -> None:
    fact = pd.DataFrame([
        {"firm_key": "NAME:X", "reporting_period": period,
         "source_reporting_period": window, "product_group": "consumer_credit",
         "canonical_sheet": "consumer_credit", "metric_name": "complaints_opened",
         "measurement_unit": "count", "metric_value": value,
         "is_analysis_ready_value": True, "is_product_level": True}
        for period, window, value in [
            ("2025-H1", "2025-01-01 to 2025-06-30", 0),
            ("2025-H2", "2025-07-01 to 2025-12-31", 5),
        ]
    ])
    firms = pd.DataFrame([{"firm_key": "NAME:X", "resolved_frn": "",
                           "display_firm_name": "Example", "identity_match_status": "unmatched",
                           "identity_match_confidence": "none"}])
    features = build_feature_tables(fact, firms)["firm_product_period_features"].sort_values("observation_end")
    assert pd.isna(features.iloc[1].pct_change_complaints_opened_count)
