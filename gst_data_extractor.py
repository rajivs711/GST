#!/usr/bin/env python3
"""GST data extractor and summarizer.

Supports JSON (list of invoice records) and CSV input files.
Extracts GST-related fields, validates GSTIN format, and produces
normalized records plus a summary.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Iterator

GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


@dataclass
class InvoiceRecord:
    invoice_id: str
    invoice_date: str
    seller_gstin: str
    buyer_gstin: str
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


def summarize(records: Iterable[InvoiceRecord]) -> dict:
    by_seller: dict[str, dict[str, float]] = defaultdict(lambda: {"invoices": 0, "taxable_value": 0.0, "total_tax": 0.0})
    invalid_gstin_count = 0

    normalized = []
    for record in records:
        if not is_valid_gstin(record.seller_gstin) or not is_valid_gstin(record.buyer_gstin):
            invalid_gstin_count += 1
        entry = by_seller[record.seller_gstin]
        entry["invoices"] += 1
        entry["taxable_value"] += record.taxable_value
        entry["total_tax"] += record.total_tax
        normalized.append(asdict(record) | {"total_tax": record.total_tax})

    return {
        "normalized_records": normalized,
        "summary_by_seller": by_seller,
        "invalid_gstin_records": invalid_gstin_count,
        "record_count": len(normalized),
    }


def write_output(result: dict, output_path: Path, output_format: str) -> None:
    if output_format == "json":
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return

    # csv output: flattened summary only
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        fields = ["seller_gstin", "invoices", "taxable_value", "total_tax"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for gstin, row in result["summary_by_seller"].items():
            writer.writerow({"seller_gstin": gstin, **row})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract and summarize GST invoice data")
    parser.add_argument("input", type=Path, help="Path to input CSV/JSON file")
    parser.add_argument("-o", "--output", type=Path, default=Path("gst_output.json"), help="Output file path")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    records = list(read_input(args.input))
    result = summarize(records)
    write_output(result, args.output, args.format)
    print(f"Processed {result['record_count']} records. Invalid GSTIN records: {result['invalid_gstin_records']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
