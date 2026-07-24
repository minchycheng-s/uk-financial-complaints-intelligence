import pandas as pd
import pytest

from customer_harm.matching.suggestions import apply_identity_overrides, apply_review_decisions


def _suggestions() -> pd.DataFrame:
    return pd.DataFrame([{
        "suggestion_id": "MATCH-1", "reporting_period": "2021-H1",
        "unmatched_firm_name": "Example Limited", "candidate_frn": "123456",
        "evidence_periods": "2025-H1", "evidence_rows": "1",
    }, {
        "suggestion_id": "MATCH-2", "reporting_period": "2021-H1",
        "unmatched_firm_name": "Example Limited", "candidate_frn": "999999",
        "evidence_periods": "2025-H1", "evidence_rows": "1",
    }])


def _crosswalk() -> pd.DataFrame:
    return pd.DataFrame([{
        "reporting_period": "2021-H1", "firm_name": "Example Limited",
        "resolved_frn": "", "match_status": "unmatched",
        "match_method": "no_exact_legal_name_reference", "match_confidence": "none",
        "candidate_frn_count": 0, "candidate_frns": "", "evidence_periods": "",
        "evidence_rows": 0,
    }])


def test_only_approved_decision_changes_crosswalk() -> None:
    decisions = pd.DataFrame([
        {"suggestion_id": "MATCH-1", "decision": "approved", "reviewer": "Analyst",
         "reviewed_at": "2026-07-18", "reviewer_comment": "Confirmed"},
        {"suggestion_id": "MATCH-2", "decision": "unresolved", "reviewer": "Analyst",
         "reviewed_at": "2026-07-18", "reviewer_comment": "Insufficient evidence"},
    ])
    updated, _ = apply_review_decisions(_suggestions(), decisions, _crosswalk())
    assert updated.iloc[0].resolved_frn == "123456"
    assert updated.iloc[0].match_method == "manually_approved_name_variant"


def test_multiple_approvals_for_one_observation_are_rejected() -> None:
    decisions = pd.DataFrame([
        {"suggestion_id": value, "decision": "approved", "reviewer": "Analyst",
         "reviewed_at": "2026-07-18", "reviewer_comment": "Confirmed"}
        for value in ["MATCH-1", "MATCH-2"]
    ])
    with pytest.raises(ValueError, match="More than one candidate"):
        apply_review_decisions(_suggestions(), decisions, _crosswalk())


def test_authoritative_identity_override_is_explicit_and_auditable() -> None:
    overrides = pd.DataFrame([{
        "reporting_period": "2021-H1", "firm_name": "Example Limited",
        "resolved_frn": "123456", "reviewer": "Analyst", "reviewed_at": "2026-01-01",
        "evidence_source": "official-register", "reviewer_comment": "Confirmed",
    }])
    result = apply_identity_overrides(_crosswalk(), overrides)
    assert result.iloc[0].resolved_frn == "123456"
    assert result.iloc[0].match_method == "reviewed_external_authoritative_evidence"
    assert result.iloc[0].match_confidence == "reviewed"
