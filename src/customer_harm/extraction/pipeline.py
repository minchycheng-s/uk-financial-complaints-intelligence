"""End-to-end, lineage-preserving FCA firm-level extraction."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import openpyxl
import pandas as pd

from customer_harm.extraction.config import ExtractionConfig
from customer_harm.extraction.mappings import MappingRegistry, normalise_label
from customer_harm.extraction.normalisation import (
    consumer_credit_measure, context_basis, identifier_name, normalise_metric_value,
    raw_text, reviewed_metric_override,
)
from customer_harm.extraction.validation import (
    build_total_reconciliation, reconciliation_issues, summarise_status, validate_metrics,
)
from customer_harm.profiling.discovery import discover_workbooks, parse_reporting_period, sha256_file

LOGGER = logging.getLogger(__name__)

OUTPUT_COLUMNS = {
    "firms": ["reporting_period", "source_reporting_period", "firm_name", "frn", "raw_firm_group", "joint_reporting_flag",
              "source_workbook", "source_sheet", "source_row"],
    "complaint_metrics": ["reporting_period", "source_reporting_period", "firm_name", "frn", "raw_firm_group",
              "joint_reporting_flag", "canonical_sheet", "metric_name", "product_group",
              "metric_value", "measurement_unit", "measurement_basis", "value_status",
              "value_reason", "raw_value", "raw_header", "source_workbook", "source_sheet",
              "source_row", "source_column"],
    "firm_aliases": ["reporting_period", "firm_name", "frn", "raw_firm_group", "trading_name",
              "value_status", "value_reason", "raw_value", "source_workbook", "source_sheet", "source_row"],
    "joint_reporters": ["reporting_period", "main_firm_name", "included_firm_name", "report_type",
              "source_reporting_period", "source_workbook", "source_sheet", "source_row"],
    "product_taxonomy": ["reporting_period", "raw_product_group", "product_group", "product_service_name",
              "reference_status", "source_workbook", "source_sheet", "source_row"],
    "rejected_records": ["reporting_period", "canonical_sheet", "reason", "raw_value", "raw_header",
              "source_workbook", "source_sheet", "source_row", "source_column"],
    "sheet_reconciliation": ["reporting_period", "canonical_sheet", "source_workbook", "source_sheet",
              "eligible_source_rows", "mapped_metric_columns", "expected_metric_records",
              "extracted_metric_records", "rejected_records", "reconciliation_status"],
}


def extract_workbooks(config: ExtractionConfig | None = None) -> dict[str, pd.DataFrame]:
    config = config or ExtractionConfig()
    inventory, gate = _load_profiling_evidence(config.profiling_dir)
    if not gate.get("extraction_authorised"):
        raise ValueError("Profiling review gate has not authorised extraction. Rerun profiling after recording decisions.")
    mappings = MappingRegistry.load(config.mappings_dir)
    rows: dict[str, list[dict[str, Any]]] = {name: [] for name in OUTPUT_COLUMNS}
    workbook_paths = {parse_reporting_period(path.name): path for path in discover_workbooks(config.input_dir)}
    expected_periods = set(inventory.reporting_period)
    if set(workbook_paths) != expected_periods:
        raise ValueError("Raw workbook periods do not match the approved profiling inventory.")

    source_hashes = {}
    for period, path in sorted(workbook_paths.items()):
        LOGGER.info("event=extract_workbook period=%s workbook=%s", period, path.name)
        source_hashes[path.name] = sha256_file(path)
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        period_inventory = inventory[inventory.reporting_period.eq(period)]
        for item in period_inventory.itertuples():
            if item.canonical_sheet not in mappings.sheets.index:
                continue
            sheet_map = mappings.sheet(item.canonical_sheet)
            ws = wb[item.sheet]
            matrix = list(ws.iter_rows(min_row=1, max_row=int(item.last_value_row),
                                       max_col=int(item.last_value_column), values_only=True))
            header_index = int(item.header_row) - 1
            headers = _unique_headers(matrix[header_index])
            data = matrix[header_index + 1:]
            entity = sheet_map["output_entity"]
            if entity in {"complaint_metric", "consumer_credit_metric"}:
                _extract_metrics(rows, data, headers, period, path.name, item.sheet,
                                 item.canonical_sheet, sheet_map, mappings, header_index + 2)
            elif entity == "firm_alias":
                _extract_aliases(rows, data, headers, period, path.name, item.sheet, header_index + 2)
            elif entity == "joint_reporter":
                _extract_joint_reporters(rows, data, headers, period, path.name, item.sheet,
                                         sheet_map["metric_name"], header_index + 2)
            elif entity == "product_reference":
                _extract_taxonomy(rows, data, headers, period, path.name, item.sheet,
                                  mappings, header_index + 2)

    frames = {name: pd.DataFrame(values, columns=columns)
              for name, (values, columns) in ((n, (rows[n], OUTPUT_COLUMNS[n])) for n in OUTPUT_COLUMNS)}
    frames["firms"] = frames["firms"].drop_duplicates().reset_index(drop=True)
    frames["total_reconciliation"] = build_total_reconciliation(frames["complaint_metrics"])
    validation_issues = validate_metrics(frames["complaint_metrics"])
    validation_issues.extend(reconciliation_issues(frames["sheet_reconciliation"],
                                                   frames["total_reconciliation"]))
    config.output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(config.output_dir / f"{name}.csv", index=False)
    pd.DataFrame(validation_issues, columns=["severity", "rule", "count", "message"]).to_csv(
        config.output_dir / "validation_issues.csv", index=False
    )
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workbooks_processed": len(workbook_paths),
        "source_hashes": source_hashes,
        "row_counts": {name: len(frame) for name, frame in frames.items()},
        "metric_value_status": summarise_status(frames["complaint_metrics"]),
        "sheet_reconciliation_status": summarise_status(frames["sheet_reconciliation"], "reconciliation_status"),
        "total_reconciliation_status": summarise_status(frames["total_reconciliation"], "reconciliation_status"),
        "validation_status": "failed" if any(i["severity"] == "error" for i in validation_issues) else "passed_with_warnings" if validation_issues else "passed",
        "validation_issues": validation_issues,
        "review_gate_status": gate["profiling_review_status"],
    }
    (config.output_dir / "extraction_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    if summary["validation_status"] == "failed":
        raise ValueError(f"Extraction validation failed: {validation_issues}")
    return frames


def _load_profiling_evidence(directory: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    inventory_path = directory / "sheet_inventory.csv"
    gate_path = directory / "profiling_review_gate.json"
    if not inventory_path.exists() or not gate_path.exists():
        raise FileNotFoundError("Profiling inventory and review gate must exist before extraction.")
    return pd.read_csv(inventory_path).fillna(""), json.loads(gate_path.read_text(encoding="utf-8"))


def _unique_headers(values: tuple[Any, ...]) -> list[str]:
    seen: dict[str, int] = {}
    result = []
    for index, value in enumerate(values, 1):
        base = str(value).strip() if value is not None and str(value).strip() else f"unnamed_{index}"
        count = seen.get(base, 0)
        seen[base] = count + 1
        result.append(base if count == 0 else f"{base}_{count + 1}")
    return result


def _identity(record: dict[str, Any]) -> dict[str, str]:
    result = {"firm_name": "", "frn": "", "raw_firm_group": "", "joint_reporting_flag": "",
              "source_reporting_period": ""}
    for header, value in record.items():
        canonical = identifier_name(header)
        if canonical in result:
            result[canonical] = raw_text(value).strip()
    return result


def _extract_metrics(rows, data, headers, period, workbook, sheet, canonical_sheet,
                     sheet_map, mappings, first_row):
    before_metrics = len(rows["complaint_metrics"])
    before_rejected = len(rows["rejected_records"])
    eligible_rows = 0
    if canonical_sheet == "consumer_credit":
        mapped_headers = [header for header in headers if consumer_credit_measure(header, period)[0]]
    else:
        mapped_headers = [header for header in headers if mappings.product_group(header) is not None]
    for offset, values in enumerate(data):
        record = dict(zip(headers, values))
        identity = _identity(record)
        source_row = first_row + offset
        if not identity["firm_name"] or normalise_label(identity["firm_name"]) in {"total", "grand total", "include"}:
            continue
        eligible_rows += 1
        rows["firms"].append({"reporting_period": period, **identity,
                              "source_workbook": workbook, "source_sheet": sheet, "source_row": source_row})
        for column, (header, value) in enumerate(zip(headers, values), 1):
            if identifier_name(header):
                continue
            product = mappings.product_group(header)
            if canonical_sheet == "consumer_credit":
                metric_name, unit = consumer_credit_measure(header, period)
                if not metric_name:
                    continue
                product = "consumer_credit"
                basis = ""
            else:
                metric_name, unit = sheet_map["metric_name"], sheet_map["measurement_unit"]
                basis = context_basis(header, canonical_sheet) if unit == "context_rate" else ""
            if product is None:
                if normalise_label(header).startswith("unnamed") or normalise_label(header) == "include":
                    continue
                rows["rejected_records"].append({"reporting_period": period, "canonical_sheet": canonical_sheet,
                    "reason": "unmapped_metric_header", "raw_value": raw_text(value), "raw_header": header,
                    "source_workbook": workbook, "source_sheet": sheet, "source_row": source_row, "source_column": column})
                continue
            metric_value, status, reason = normalise_metric_value(value)
            override = reviewed_metric_override(value, period, canonical_sheet, product)
            if override:
                status, reason = override
            rows["complaint_metrics"].append({"reporting_period": period, **identity,
                "canonical_sheet": canonical_sheet, "metric_name": metric_name, "product_group": product,
                "metric_value": metric_value, "measurement_unit": unit, "measurement_basis": basis,
                "value_status": status, "value_reason": reason, "raw_value": raw_text(value),
                "raw_header": header, "source_workbook": workbook, "source_sheet": sheet,
                "source_row": source_row, "source_column": column})
    extracted = len(rows["complaint_metrics"]) - before_metrics
    rejected = len(rows["rejected_records"]) - before_rejected
    expected = eligible_rows * len(mapped_headers)
    rows["sheet_reconciliation"].append({"reporting_period": period,
        "canonical_sheet": canonical_sheet, "source_workbook": workbook, "source_sheet": sheet,
        "eligible_source_rows": eligible_rows, "mapped_metric_columns": len(mapped_headers),
        "expected_metric_records": expected, "extracted_metric_records": extracted,
        "rejected_records": rejected,
        "reconciliation_status": "matched" if expected == extracted and rejected == 0 else "mismatch"})


def _extract_aliases(rows, data, headers, period, workbook, sheet, first_row):
    for offset, values in enumerate(data):
        record = dict(zip(headers, values)); identity = _identity(record)
        if not identity["firm_name"]:
            continue
        alias_header = next((h for h in headers if "trading name" in normalise_label(h)), "")
        value = record.get(alias_header)
        text = raw_text(value).strip()
        if normalise_label(text) == "null":
            alias, status, reason = "", "missing_marker", "source_null_literal"
        elif text == "0":
            alias, status, reason = "", "missing_marker", "source_zero_placeholder"
        elif not text:
            alias, status, reason = "", "missing", "blank_source_cell"
        else:
            alias, status, reason = text, "valid", ""
        source_row = first_row + offset
        rows["firms"].append({"reporting_period": period, **identity,
                              "source_workbook": workbook, "source_sheet": sheet, "source_row": source_row})
        rows["firm_aliases"].append({"reporting_period": period, **{k: identity[k] for k in ("firm_name", "frn", "raw_firm_group")},
            "trading_name": alias, "value_status": status, "value_reason": reason, "raw_value": text,
            "source_workbook": workbook, "source_sheet": sheet, "source_row": source_row})


def _extract_joint_reporters(rows, data, headers, period, workbook, sheet, report_type, first_row):
    firm_header = next((h for h in headers if normalise_label(h) == "firm name"), "")
    included_header = next((h for h in headers if "other firms included" in normalise_label(h)), "")
    period_header = next((h for h in headers if normalise_label(h) == "reporting period"), "")
    for offset, values in enumerate(data):
        record = dict(zip(headers, values)); main = raw_text(record.get(firm_header)).strip()
        included = raw_text(record.get(included_header)).strip()
        if not main or not included:
            continue
        rows["joint_reporters"].append({"reporting_period": period, "main_firm_name": main,
            "included_firm_name": included, "report_type": report_type,
            "source_reporting_period": raw_text(record.get(period_header)).strip(),
            "source_workbook": workbook, "source_sheet": sheet, "source_row": first_row + offset})


def _extract_taxonomy(rows, data, headers, period, workbook, sheet, mappings, first_row):
    group_header = next((h for h in headers if normalise_label(h) == "product group"), "")
    product_header = next((h for h in headers if "product/service" in normalise_label(h)), "")
    inherited = ""
    for offset, values in enumerate(data):
        record = dict(zip(headers, values)); raw_group = raw_text(record.get(group_header)).strip()
        product = raw_text(record.get(product_header)).strip()
        if raw_group:
            inherited = raw_group
        if not product:
            continue
        canonical = mappings.product_group(inherited)
        rows["product_taxonomy"].append({"reporting_period": period,
            "raw_product_group": inherited, "product_group": canonical or "unmapped",
            "product_service_name": product, "reference_status": "confirmed_in_source",
            "source_workbook": workbook, "source_sheet": sheet, "source_row": first_row + offset})
