import pandas as pd

from customer_harm.external_context.reporting import (
    build_economic_context_dashboard,
    build_product_period_context_dashboard,
    validate_context_reporting,
)


def test_economic_context_has_one_row_per_period() -> None:
    boe = pd.DataFrame([
        {"reporting_period": "2025-H1", "period_start": "2025-01-01",
         "start_bank_rate": 4.75, "end_bank_rate": 4.25},
        {"reporting_period": "2025-H2", "period_start": "2025-07-01",
         "start_bank_rate": 4.25, "end_bank_rate": 3.75},
    ])
    ons = pd.DataFrame([
        {"reporting_period": period, "indicator_name": indicator,
         "period_end_value": end, "period_mean": mean}
        for period, indicator, end, mean in [
            ("2025-H1", "cpi", 3.6, 3.4),
            ("2025-H1", "insurance", -1.0, 0.2),
            ("2025-H2", "cpi", 3.4, 3.6),
            ("2025-H2", "insurance", -2.6, -3.4),
        ]
    ])
    result = build_economic_context_dashboard(boe, ons)
    assert len(result) == 2
    assert result.reporting_period.is_unique
    assert result.loc[result.reporting_period.eq("2025-H2"), "cpi_period_end"].iloc[0] == 3.4


def test_product_context_uses_sum_for_counts_and_median_for_rates() -> None:
    source = pd.DataFrame([
        {
            "firm_key": firm, "reporting_period": period,
            "product_group": "home_finance", "product_group_label": "Home Finance",
            "display_order": 4, "complaints_opened_count": opened,
            "complaints_upheld_pct": upheld, "closed_within_3_days_pct": 0.5,
            "closed_after_3_days_within_8_weeks_pct": 0.4,
            "context_provision_rate": 2.0, "context_intermediation_rate": None,
            "is_priority_review": priority, "has_current_signal": priority,
            "is_source_anomaly": False,
            "priority_band": "priority_review" if priority else "no_current_signal",
        }
        for period, firm, opened, upheld, priority in [
            ("2025-H1", "A", 10, 0.2, False),
            ("2025-H1", "B", 30, 0.8, True),
            ("2025-H2", "A", 20, 0.4, False),
            ("2025-H2", "B", 40, 0.6, False),
        ]
    ])
    result = build_product_period_context_dashboard(source)
    first = result.loc[result.reporting_period.eq("2025-H1")].iloc[0]
    second = result.loc[result.reporting_period.eq("2025-H2")].iloc[0]
    assert first.complaints_opened_total == 40
    assert first.complaints_upheld_pct_median == 0.5
    assert first.priority_review_observations == 1
    assert second.change_complaints_opened_total == 20
    assert second.pct_change_complaints_opened_total == 0.5


def test_context_reporting_validation_accepts_complete_grains() -> None:
    economic = pd.DataFrame({"reporting_period": ["2025-H1", "2025-H2"]})
    product = pd.DataFrame([
        {"reporting_period": period, "product_group": product,
         "distinct_firm_count": 1, "firm_observation_count": 1,
         "priority_review_observations": 0}
        for period in ["2025-H1", "2025-H2"]
        for product in ["home_finance", "insurance"]
    ])
    assert validate_context_reporting(economic, product, 2, 2) == []
