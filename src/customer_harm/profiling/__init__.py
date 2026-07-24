"""Workbook profiling public API."""

from customer_harm.profiling.discovery import discover_workbooks, parse_reporting_period
from customer_harm.profiling.headers import detect_header, score_header_candidates
from customer_harm.profiling.pipeline import ProfileConfig, ProfilingRunError, profile_workbooks

__all__ = [
    "ProfileConfig",
    "ProfilingRunError",
    "detect_header",
    "discover_workbooks",
    "parse_reporting_period",
    "profile_workbooks",
    "score_header_candidates",
]
