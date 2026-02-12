# GST Data Extractor

A lightweight command-line utility to extract, validate, and summarize GST invoice data from CSV or JSON files.

## Features

- Reads invoice data from `.csv` or `.json`.
- Normalizes core GST fields.
- Validates seller and buyer GSTIN format.
- Creates seller-wise summary totals.
- Exports output in JSON (detailed) or CSV (summary).

## Input schema

Each record should include:

- `invoice_id`
- `invoice_date`
- `seller_gstin`
- `buyer_gstin`
- `taxable_value`
- `cgst`
- `sgst`
- `igst`

## Usage

```bash
python3 gst_data_extractor.py invoices.json -o output.json --format json
python3 gst_data_extractor.py invoices.csv -o summary.csv --format csv
```

## Test

```bash
python3 -m unittest discover -s tests -v
```
