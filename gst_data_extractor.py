#!/usr/bin/env python3
"""GST data extractor and summarizer.

Supports JSON (list of invoice records) and CSV input files.
Extracts GST-related fields, validates GSTIN format, and produces
normalized records plus summary views for seller-wise and HSN-wise
reporting (useful for GSTR-1 filing).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator

GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


@dataclass
class InvoiceRecord:
    invoice_id: str
    invoice_date: str
    seller_gstin: str
    buyer_gstin: str
    hsn_code: str
    taxable_value: float
    cgst: float
    sgst: float
    igst: float

    @property
    def total_tax(self) -> float:
        return self.cgst + self.sgst + self.igst



def is_valid_gstin(value: str) -> bool:
    return bool(value and GSTIN_PATTERN.fullmatch(value.strip().upper()))



def _to_float(value: object, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    return float(value)



def normalize_record(raw: dict) -> InvoiceRecord:
    return InvoiceRecord(
        invoice_id=str(raw.get("invoice_id", "")).strip(),
        invoice_date=str(raw.get("invoice_date", "")).strip(),
        seller_gstin=str(raw.get("seller_gstin", "")).strip().upper(),
        buyer_gstin=str(raw.get("buyer_gstin", "")).strip().upper(),
        hsn_code=str(raw.get("hsn_code", "UNKNOWN")).strip().upper() or "UNKNOWN",
        taxable_value=_to_float(raw.get("taxable_value", 0)),
        cgst=_to_float(raw.get("cgst", 0)),
        sgst=_to_float(raw.get("sgst", 0)),
        igst=_to_float(raw.get("igst", 0)),
    )



def read_input(path: Path) -> Iterator[InvoiceRecord]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("JSON input must be a list of invoice objects")
        for row in payload:
            if isinstance(row, dict):
                yield normalize_record(row)
    elif suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                yield normalize_record(row)
    else:
        raise ValueError("Unsupported file type. Use .csv or .json")



def _empty_summary_row() -> dict[str, float]:
    return {"invoices": 0, "taxable_value": 0.0, "cgst": 0.0, "sgst": 0.0, "igst": 0.0, "total_tax": 0.0}



def summarize(records: Iterable[InvoiceRecord]) -> dict:
    by_seller: dict[str, dict[str, float]] = defaultdict(_empty_summary_row)
    by_hsn: dict[str, dict[str, float]] = defaultdict(_empty_summary_row)
    invalid_gstin_count = 0

    normalized = []
    for record in records:
        if not is_valid_gstin(record.seller_gstin) or not is_valid_gstin(record.buyer_gstin):
            invalid_gstin_count += 1

        seller_entry = by_seller[record.seller_gstin]
        seller_entry["invoices"] += 1
        seller_entry["taxable_value"] += record.taxable_value
        seller_entry["cgst"] += record.cgst
        seller_entry["sgst"] += record.sgst
        seller_entry["igst"] += record.igst
        seller_entry["total_tax"] += record.total_tax

        hsn_entry = by_hsn[record.hsn_code]
        hsn_entry["invoices"] += 1
        hsn_entry["taxable_value"] += record.taxable_value
        hsn_entry["cgst"] += record.cgst
        hsn_entry["sgst"] += record.sgst
        hsn_entry["igst"] += record.igst
        hsn_entry["total_tax"] += record.total_tax

        normalized.append(asdict(record) | {"total_tax": record.total_tax})

    return {
        "normalized_records": normalized,
        "summary_by_seller": by_seller,
        "summary_by_hsn": by_hsn,
        "invalid_gstin_records": invalid_gstin_count,
        "record_count": len(normalized),
    }



def write_output(result: dict, output_path: Path, output_format: str, report: str) -> None:
    if output_format == "json":
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return

    if report == "seller":
        key = "summary_by_seller"
        first_col = "seller_gstin"
    else:
        key = "summary_by_hsn"
        first_col = "hsn_code"

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        fields = [first_col, "invoices", "taxable_value", "cgst", "sgst", "igst", "total_tax"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for group_value, row in result[key].items():
            writer.writerow({first_col: group_value, **row})



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract and summarize GST invoice data")
    parser.add_argument("input", type=Path, help="Path to input CSV/JSON file")
    parser.add_argument("-o", "--output", type=Path, default=Path("gst_output.json"), help="Output file path")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument(
        "--report",
        choices=["seller", "hsn"],
        default="seller",
        help="For CSV output, choose summary grouping: seller or hsn",
    )
    return parser



def main() -> int:
    args = build_parser().parse_args()
    records = list(read_input(args.input))
    result = summarize(records)
    write_output(result, args.output, args.format, args.report)
    print(
        "Processed "
        f"{result['record_count']} records. "
        f"Invalid GSTIN records: {result['invalid_gstin_records']}. "
        f"HSN groups: {len(result['summary_by_hsn'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
