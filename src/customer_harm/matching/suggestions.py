"""Generate non-authoritative possible firm matches for human review."""

from __future__ import annotations

import hashlib
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import pandas as pd

from customer_harm.matching.resolution import normalise_firm_name
from customer_harm.matching.resolution import enrich_metrics

LEGAL_FORM_EQUIVALENTS = {
    "limited": "ltd", "ltd": "ltd", "public limited company": "plc", "plc": "plc",
    "incorporated": "inc", "inc": "inc", "corporation": "corp", "corp": "corp",
}


def comparison_key(value: object) -> str:
    """Create a loose key for ranking only; it is never used to approve a match."""
    text = normalise_firm_name(value).replace("&", " and ")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for phrase, replacement in sorted(LEGAL_FORM_EQUIVALENTS.items(), key=lambda item: -len(item[0])):
        text = re.sub(rf"\b{re.escape(phrase)}\b", replacement, text)
    return re.sub(r"\s+", " ", text).strip()


def score_names(source: str, candidate: str) -> tuple[float, float, float]:
    left, right = comparison_key(source), comparison_key(candidate)
    character = SequenceMatcher(None, left, right).ratio()
    token = SequenceMatcher(None, " ".join(sorted(left.split())),
                            " ".join(sorted(right.split()))).ratio()
    combined = 0.65 * character + 0.35 * token
    return round(character, 6), round(token, 6), round(combined, 6)


def build_candidate_reference(aliases: pd.DataFrame) -> pd.DataFrame:
    """Create legal- and trading-name candidates backed by a source FRN."""
    source = aliases[aliases.frn.fillna("").astype(str).str.strip().ne("")].copy()
    source["frn"] = source.frn.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    legal = source[["firm_name", "frn", "reporting_period"]].rename(
        columns={"firm_name": "candidate_name"}
    )
    legal["candidate_legal_name"] = legal.candidate_name
    legal["candidate_name_type"] = "legal_name"
    trading = source[source.trading_name.fillna("").astype(str).str.strip().ne("")][
        ["trading_name", "firm_name", "frn", "reporting_period"]
    ].rename(columns={"trading_name": "candidate_name", "firm_name": "candidate_legal_name"})
    trading["candidate_name_type"] = "trading_name"
    candidates = pd.concat([legal, trading], ignore_index=True)
    candidates["candidate_name"] = candidates.candidate_name.astype(str).str.strip()
    candidates = candidates[candidates.candidate_name.ne("")]
    grouped = candidates.groupby(
        ["candidate_name", "candidate_legal_name", "candidate_name_type", "frn"],
        as_index=False, dropna=False
    ).agg(evidence_periods=("reporting_period", lambda values: "|".join(sorted(set(values)))),
          evidence_rows=("reporting_period", "size"))
    return grouped


def generate_suggestions(unmatched: pd.DataFrame, aliases: pd.DataFrame,
                         suggestions_per_firm: int = 3) -> pd.DataFrame:
    candidates = build_candidate_reference(aliases)
    candidates["comparison_key_value"] = candidates.candidate_name.map(comparison_key)
    candidates["token_set"] = candidates.comparison_key_value.map(lambda value: frozenset(value.split()))
    records: list[dict[str, Any]] = []
    for source in unmatched[["reporting_period", "firm_name"]].drop_duplicates().itertuples(index=False):
        source_key = comparison_key(source.firm_name)
        source_tokens = frozenset(source_key.split())
        # Token overlap and length are inexpensive and reduce the detailed SequenceMatcher
        # work while retaining suffix, punctuation and word-order variants in the shortlist.
        shortlist_scores = []
        for candidate in candidates.itertuples(index=False):
            union = source_tokens | candidate.token_set
            overlap = len(source_tokens & candidate.token_set) / len(union) if union else 0
            length_ratio = min(len(source_key), len(candidate.comparison_key_value)) / max(
                len(source_key), len(candidate.comparison_key_value), 1
            )
            shortlist_scores.append((0.8 * overlap + 0.2 * length_ratio, candidate))
        shortlist_scores.sort(key=lambda item: -item[0])
        ranked = []
        for _, candidate in shortlist_scores[:250]:
            character, token, combined = score_names(source.firm_name, candidate.candidate_name)
            ranked.append((combined, character, token, candidate))
        ranked.sort(key=lambda item: (-item[0], -item[1], item[3].candidate_name, item[3].frn))
        distinct_ranked = []
        seen_frns = set()
        for item in ranked:
            candidate = item[3]
            if candidate.frn in seen_frns:
                continue
            seen_frns.add(candidate.frn)
            distinct_ranked.append(item)
            if len(distinct_ranked) == suggestions_per_firm:
                break
        for rank, (combined, character, token, candidate) in enumerate(distinct_ranked, 1):
            stable = "|".join([source.reporting_period, source.firm_name,
                               candidate.candidate_name, candidate.frn])
            suggestion_id = "MATCH-" + hashlib.sha256(stable.encode("utf-8")).hexdigest()[:12].upper()
            quality = "high_similarity" if combined >= 0.9 else "medium_similarity" if combined >= 0.75 else "low_similarity"
            records.append({"suggestion_id": suggestion_id,
                "reporting_period": source.reporting_period, "unmatched_firm_name": source.firm_name,
                "suggestion_rank": rank, "candidate_name": candidate.candidate_name,
                "candidate_legal_name": candidate.candidate_legal_name,
                "candidate_name_type": candidate.candidate_name_type, "candidate_frn": candidate.frn,
                "character_similarity": character, "token_similarity": token,
                "combined_score": combined, "suggestion_quality": quality,
                "evidence_periods": candidate.evidence_periods,
                "evidence_rows": candidate.evidence_rows, "review_status": "pending_review"})
    columns = ["suggestion_id", "reporting_period", "unmatched_firm_name", "suggestion_rank",
               "candidate_name", "candidate_legal_name", "candidate_name_type", "candidate_frn",
               "character_similarity", "token_similarity", "combined_score", "suggestion_quality",
               "evidence_periods", "evidence_rows", "review_status"]
    return pd.DataFrame(records, columns=columns)


def build_grouped_review_queue(suggestions: pd.DataFrame) -> pd.DataFrame:
    """Collapse repeated period observations into a shorter analyst review queue."""
    top = suggestions[suggestions.suggestion_rank.astype(int).eq(1)].copy()
    top["exact_comparison_key"] = top.apply(
        lambda row: comparison_key(row.unmatched_firm_name) == comparison_key(row.candidate_name), axis=1
    )
    records = []
    for firm_name, group in top.groupby("unmatched_firm_name", sort=True):
        candidate_groups = group.groupby(
            ["candidate_frn", "candidate_name", "candidate_legal_name", "candidate_name_type"],
            dropna=False, sort=False
        )
        candidate_key, candidate_rows = max(candidate_groups, key=lambda item: len(item[1]))
        frn, candidate_name, legal_name, name_type = candidate_key
        exact = bool(candidate_rows.exact_comparison_key.all())
        score = float(candidate_rows.combined_score.astype(float).max())
        if exact:
            tier, action, basis = (
                "A", "confirm_legal_identity_then_approve",
                "Names become identical after punctuation and legal-form standardisation."
            )
        elif score >= 0.9:
            tier, action, basis = (
                "B", "investigate_name_difference",
                "High text similarity, but small differences can still identify a different firm."
            )
        elif score >= 0.75:
            tier, action, basis = (
                "C", "seek_authoritative_rename_or_trading_name_evidence",
                "Moderate similarity requires external identity evidence."
            )
        else:
            tier, action, basis = (
                "D", "leave_unmatched_unless_new_evidence_found",
                "Low similarity is not a credible identity basis by itself."
            )
        records.append({"unmatched_firm_name": firm_name,
            "affected_reporting_periods": "|".join(sorted(group.reporting_period.unique())),
            "affected_period_count": group.reporting_period.nunique(),
            "priority_tier": tier, "recommended_action": action,
            "recommendation_basis": basis, "top_candidate_name": candidate_name,
            "top_candidate_legal_name": legal_name, "top_candidate_name_type": name_type,
            "top_candidate_frn": frn, "top_combined_score": score,
            "top_candidate_consistent_across_periods": group.candidate_frn.nunique() == 1,
            "review_status": "pending_review"})
    columns = ["unmatched_firm_name", "affected_reporting_periods", "affected_period_count",
               "priority_tier", "recommended_action", "recommendation_basis",
               "top_candidate_name", "top_candidate_legal_name", "top_candidate_name_type",
               "top_candidate_frn", "top_combined_score", "top_candidate_consistent_across_periods",
               "review_status"]
    return pd.DataFrame(records, columns=columns).sort_values(
        ["priority_tier", "unmatched_firm_name"]
    ).reset_index(drop=True)


def run_suggestion_generation(resolved_dir: Path, extracted_dir: Path,
                              output_dir: Path, decisions_path: Path,
                              suggestions_per_firm: int = 3) -> dict[str, Any]:
    unmatched_path = resolved_dir / "unmatched_firms.csv"
    aliases_path = extracted_dir / "firm_aliases.csv"
    if not unmatched_path.exists() or not aliases_path.exists():
        raise FileNotFoundError("unmatched_firms.csv and firm_aliases.csv are required.")
    unmatched = pd.read_csv(unmatched_path, dtype=str).fillna("")
    aliases = pd.read_csv(aliases_path, dtype=str).fillna("")
    suggestions = generate_suggestions(unmatched, aliases, suggestions_per_firm)
    review_queue = build_grouped_review_queue(suggestions)
    output_dir.mkdir(parents=True, exist_ok=True)
    suggestions.to_csv(output_dir / "firm_match_suggestions.csv", index=False)
    review_queue.to_csv(output_dir / "firm_match_review_queue.csv", index=False)
    if not decisions_path.exists():
        decisions_path.parent.mkdir(parents=True, exist_ok=True)
        decisions_path.write_text(
            "suggestion_id,decision,reviewer,reviewed_at,reviewer_comment\n", encoding="utf-8"
        )
    summary = {"unmatched_period_firm_pairs": len(unmatched),
               "suggestions_generated": len(suggestions),
               "suggestions_per_firm": suggestions_per_firm,
               "quality_counts": suggestions.suggestion_quality.value_counts().to_dict(),
               "unique_firms_to_review": len(review_queue),
               "review_priority_counts": review_queue.priority_tier.value_counts().sort_index().to_dict(),
               "all_suggestions_pending_review": bool(suggestions.review_status.eq("pending_review").all()),
               "automatic_matches_applied": 0}
    (output_dir / "firm_match_suggestion_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def apply_review_decisions(suggestions: pd.DataFrame, decisions: pd.DataFrame,
                           crosswalk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply only explicit approved suggestions to a copy of the identity crosswalk."""
    required = {"suggestion_id", "decision", "reviewer", "reviewed_at", "reviewer_comment"}
    if not required <= set(decisions.columns):
        raise ValueError(f"Review decisions lack columns: {sorted(required - set(decisions.columns))}")
    allowed = {"approved", "rejected", "unresolved"}
    invalid = set(decisions.decision) - allowed
    if invalid:
        raise ValueError(f"Invalid firm match decisions: {sorted(invalid)}")
    if decisions.suggestion_id.duplicated().any():
        raise ValueError("Firm match decisions contain duplicate suggestion IDs.")
    unknown = set(decisions.suggestion_id) - set(suggestions.suggestion_id)
    if unknown:
        raise ValueError(f"Decisions reference unknown suggestions: {sorted(unknown)[:5]}")
    approved_metadata_missing = decisions.decision.eq("approved") & (
        decisions.reviewer.eq("") | decisions.reviewed_at.eq("")
    )
    if approved_metadata_missing.any():
        raise ValueError("Approved firm matches require reviewer and reviewed_at metadata.")
    reviewed = suggestions.merge(decisions, on="suggestion_id", how="left", validate="one_to_one")
    reviewed["decision"] = reviewed.decision.fillna("unreviewed")
    approved = reviewed[reviewed.decision.eq("approved")]
    keys = ["reporting_period", "unmatched_firm_name"]
    if approved.duplicated(keys).any():
        raise ValueError("More than one candidate is approved for an unmatched firm observation.")

    updated = crosswalk.copy()
    for row in approved.itertuples(index=False):
        mask = (updated.reporting_period.eq(row.reporting_period) &
                updated.firm_name.eq(row.unmatched_firm_name))
        if mask.sum() != 1:
            raise ValueError(f"Approved suggestion has no unique crosswalk row: {row.suggestion_id}")
        updated.loc[mask, "resolved_frn"] = str(row.candidate_frn)
        updated.loc[mask, "match_status"] = "matched"
        updated.loc[mask, "match_method"] = "manually_approved_name_variant"
        updated.loc[mask, "match_confidence"] = "reviewed"
        updated.loc[mask, "candidate_frn_count"] = 1
        updated.loc[mask, "candidate_frns"] = str(row.candidate_frn)
        updated.loc[mask, "evidence_periods"] = str(row.evidence_periods)
        updated.loc[mask, "evidence_rows"] = int(row.evidence_rows)
    return updated, reviewed


def apply_identity_overrides(crosswalk: pd.DataFrame,
                             overrides: pd.DataFrame) -> pd.DataFrame:
    """Apply separately evidenced exact identity overrides at period/name grain."""
    required = {"reporting_period", "firm_name", "resolved_frn", "reviewer",
                "reviewed_at", "evidence_source", "reviewer_comment"}
    if not required <= set(overrides.columns):
        raise ValueError(f"Identity overrides lack columns: {sorted(required - set(overrides.columns))}")
    keys = ["reporting_period", "firm_name"]
    if overrides.duplicated(keys).any():
        raise ValueError("Identity overrides contain duplicate period/name keys.")
    if (overrides.resolved_frn.eq("") | overrides.reviewer.eq("") |
            overrides.reviewed_at.eq("") | overrides.evidence_source.eq("")).any():
        raise ValueError("Identity overrides require FRN, reviewer, date and evidence source.")
    updated = crosswalk.copy()
    for row in overrides.itertuples(index=False):
        mask = (updated.reporting_period.eq(row.reporting_period) &
                updated.firm_name.eq(row.firm_name))
        if mask.sum() != 1:
            raise ValueError(f"Identity override has no unique crosswalk row: "
                             f"{row.reporting_period}/{row.firm_name}")
        updated.loc[mask, "resolved_frn"] = str(row.resolved_frn)
        updated.loc[mask, "match_status"] = "matched"
        updated.loc[mask, "match_method"] = "reviewed_external_authoritative_evidence"
        updated.loc[mask, "match_confidence"] = "reviewed"
        updated.loc[mask, "candidate_frn_count"] = 1
        updated.loc[mask, "candidate_frns"] = str(row.resolved_frn)
        updated.loc[mask, "evidence_periods"] = str(row.reporting_period)
        updated.loc[mask, "evidence_rows"] = 1
    return updated


def run_review_application(resolved_dir: Path, extracted_dir: Path,
                           decisions_path: Path,
                           overrides_path: Path | None = None) -> dict[str, Any]:
    suggestions = pd.read_csv(resolved_dir / "firm_match_suggestions.csv", dtype=str).fillna("")
    decisions = pd.read_csv(decisions_path, dtype=str).fillna("")
    crosswalk = pd.read_csv(resolved_dir / "firm_identity_crosswalk.csv", dtype=str).fillna("")
    metrics = pd.read_csv(extracted_dir / "complaint_metrics.csv", dtype={"frn": str}, low_memory=False)
    updated, reviewed = apply_review_decisions(suggestions, decisions, crosswalk)
    override_count = 0
    if overrides_path is not None and overrides_path.exists():
        overrides = pd.read_csv(overrides_path, dtype=str).fillna("")
        updated = apply_identity_overrides(updated, overrides)
        override_count = len(overrides)
    enriched = enrich_metrics(metrics, updated)
    updated.to_csv(resolved_dir / "firm_identity_crosswalk_reviewed.csv", index=False)
    enriched.to_csv(resolved_dir / "complaint_metrics_resolved_reviewed.csv", index=False)
    reviewed.to_csv(resolved_dir / "firm_match_review_results.csv", index=False)
    updated[updated.match_status.eq("unmatched")].to_csv(
        resolved_dir / "unmatched_firms_after_review.csv", index=False
    )
    summary = {"suggestions": len(suggestions), "decisions_recorded": len(decisions),
               "decision_counts": decisions.decision.value_counts().to_dict(),
               "approved_matches_applied": int(decisions.decision.eq("approved").sum()),
               "identity_overrides_applied": override_count,
               "remaining_unmatched_period_firm_pairs": int(updated.match_status.eq("unmatched").sum()),
               "metric_rows_input": len(metrics), "metric_rows_output": len(enriched),
               "row_count_preserved": len(metrics) == len(enriched)}
    (resolved_dir / "firm_match_review_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary
