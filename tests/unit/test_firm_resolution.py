import pandas as pd

from customer_harm.matching.resolution import (
    build_firm_crosswalk, enrich_metrics, normalise_firm_name,
)


def test_name_normalisation_preserves_punctuation() -> None:
    assert normalise_firm_name("  Example   Firm, Ltd. ") == "example firm, ltd."


def test_unique_exact_name_resolves_to_frn() -> None:
    metrics = pd.DataFrame([{"reporting_period": "2022-H1", "firm_name": "Example Firm"}])
    aliases = pd.DataFrame([{"reporting_period": "2025-H1", "firm_name": " example  firm ",
                             "frn": "123456"}])
    result = build_firm_crosswalk(metrics, aliases).iloc[0]
    assert result.resolved_frn == "123456"
    assert result.match_method == "exact_name_global_unique"
    assert result.match_confidence == "medium"


def test_multiple_frns_are_ambiguous_and_unassigned() -> None:
    metrics = pd.DataFrame([{"reporting_period": "2025-H1", "firm_name": "Same Name"}])
    aliases = pd.DataFrame([
        {"reporting_period": "2025-H1", "firm_name": "Same Name", "frn": "111111"},
        {"reporting_period": "2025-H1", "firm_name": "Same Name", "frn": "222222"},
    ])
    result = build_firm_crosswalk(metrics, aliases).iloc[0]
    assert result.match_status == "ambiguous"
    assert result.resolved_frn == ""
    assert result.match_confidence == "none"
    assert result.candidate_frn_count == 2


def test_enrichment_preserves_metric_rows() -> None:
    metrics = pd.DataFrame([
        {"reporting_period": "2025-H1", "firm_name": "Example", "metric_value": 1},
        {"reporting_period": "2025-H1", "firm_name": "Example", "metric_value": 2},
    ])
    crosswalk = pd.DataFrame([{"reporting_period": "2025-H1", "firm_name": "Example",
                               "resolved_frn": "123456", "match_status": "matched",
                               "match_method": "exact_name_same_period", "match_confidence": "high"}])
    result = enrich_metrics(metrics, crosswalk)
    assert len(result) == 2
    assert set(result.resolved_frn) == {"123456"}
