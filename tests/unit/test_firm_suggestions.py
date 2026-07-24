import pandas as pd

from customer_harm.matching.suggestions import (
    build_grouped_review_queue, comparison_key, generate_suggestions,
)


def test_comparison_key_standardises_legal_form_for_ranking() -> None:
    assert comparison_key("Example Limited") == comparison_key("Example Ltd")


def test_suggestions_remain_pending_and_rank_best_candidate_first() -> None:
    unmatched = pd.DataFrame([{"reporting_period": "2021-H1",
                               "firm_name": "Example Financial Services Limited"}])
    aliases = pd.DataFrame([
        {"reporting_period": "2025-H1", "firm_name": "Example Financial Services Ltd",
         "trading_name": "", "frn": "111111"},
        {"reporting_period": "2025-H1", "firm_name": "Completely Different Plc",
         "trading_name": "", "frn": "222222"},
    ])
    suggestions = generate_suggestions(unmatched, aliases, suggestions_per_firm=2)
    assert suggestions.iloc[0].candidate_frn == "111111"
    assert suggestions.iloc[0].suggestion_rank == 1
    assert set(suggestions.review_status) == {"pending_review"}


def test_trading_names_are_labelled_as_trading_name_evidence() -> None:
    unmatched = pd.DataFrame([{"reporting_period": "2021-H1", "firm_name": "Example Brand"}])
    aliases = pd.DataFrame([{"reporting_period": "2025-H1", "firm_name": "Legal Entity Ltd",
                             "trading_name": "Example Brand", "frn": "333333"}])
    result = generate_suggestions(unmatched, aliases, suggestions_per_firm=1).iloc[0]
    assert result.candidate_name_type == "trading_name"
    assert result.candidate_legal_name == "Legal Entity Ltd"
    assert result.review_status == "pending_review"


def test_grouped_queue_collapses_periods_and_keeps_decision_pending() -> None:
    unmatched = pd.DataFrame([
        {"reporting_period": "2021-H1", "firm_name": "Example Limited"},
        {"reporting_period": "2021-H2", "firm_name": "Example Limited"},
    ])
    aliases = pd.DataFrame([{"reporting_period": "2025-H1", "firm_name": "Example Ltd",
                             "trading_name": "", "frn": "123456"}])
    queue = build_grouped_review_queue(generate_suggestions(unmatched, aliases, 1))
    assert len(queue) == 1
    assert queue.iloc[0].affected_period_count == 2
    assert queue.iloc[0].priority_tier == "A"
    assert queue.iloc[0].review_status == "pending_review"
