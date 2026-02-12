# GST Data Extractor

A lightweight command-line utility to extract, validate, and summarize GST invoice data from CSV or JSON files.

## Features

- Reads invoice data from `.csv` or `.json`.
- Normalizes core GST fields.
- Validates seller and buyer GSTIN format.
- Creates seller-wise summary totals.
- Provides **HSN-wise totals** for GSTR-1 filing support.
- Exports output in JSON (detailed) or CSV (summary by seller or HSN).

## Input schema

Each record should include:

- `invoice_id`
- `invoice_date`
- `seller_gstin`
- `buyer_gstin`
- `hsn_code` (recommended for GSTR-1 HSN summary)
- `taxable_value`
- `cgst`
- `sgst`
- `igst`

## Usage

```bash
python3 gst_data_extractor.py invoices.json -o output.json --format json
python3 gst_data_extractor.py invoices.csv -o seller_summary.csv --format csv --report seller
python3 gst_data_extractor.py invoices.csv -o hsn_summary.csv --format csv --report hsn
```

## Output notes

- JSON output contains:
  - `normalized_records`
  - `summary_by_seller`
  - `summary_by_hsn`
  - `invalid_gstin_records`
  - `record_count`
- CSV output uses `--report seller|hsn` to choose grouping.

## Test

```bash
python3 -m unittest discover -s tests -v
```
