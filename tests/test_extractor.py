import csv
import json
import tempfile
import unittest
from pathlib import Path

from gst_data_extractor import is_valid_gstin, read_input, summarize, write_output


class TestGSTExtractor(unittest.TestCase):
    def test_gstin_validation(self):
        self.assertTrue(is_valid_gstin("29ABCDE1234F1Z5"))
        self.assertFalse(is_valid_gstin("INVALIDGST"))

    def test_summary_json_input_with_hsn(self):
        sample = [
            {
                "invoice_id": "INV-1",
                "invoice_date": "2025-01-05",
                "seller_gstin": "29ABCDE1234F1Z5",
                "buyer_gstin": "27PQRSX5678L1Z2",
                "hsn_code": "1001",
                "taxable_value": 1000,
                "cgst": 90,
                "sgst": 90,
                "igst": 0,
            },
            {
                "invoice_id": "INV-2",
                "invoice_date": "2025-01-07",
                "seller_gstin": "29ABCDE1234F1Z5",
                "buyer_gstin": "07AAAAA0000A1Z5",
                "hsn_code": "1001",
                "taxable_value": 500,
                "cgst": 45,
                "sgst": 45,
                "igst": 0,
            },
        ]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invoices.json"
            path.write_text(json.dumps(sample), encoding="utf-8")
            records = list(read_input(path))
            result = summarize(records)

        self.assertEqual(result["record_count"], 2)
        self.assertEqual(result["invalid_gstin_records"], 0)

        seller = result["summary_by_seller"]["29ABCDE1234F1Z5"]
        self.assertEqual(seller["invoices"], 2)
        self.assertEqual(seller["taxable_value"], 1500)
        self.assertEqual(seller["total_tax"], 270)

        hsn = result["summary_by_hsn"]["1001"]
        self.assertEqual(hsn["invoices"], 2)
        self.assertEqual(hsn["taxable_value"], 1500)
        self.assertEqual(hsn["cgst"], 135)

    def test_csv_hsn_report_output(self):
        result = {
            "summary_by_seller": {},
            "summary_by_hsn": {
                "1001": {
                    "invoices": 3,
                    "taxable_value": 1200.0,
                    "cgst": 54.0,
                    "sgst": 54.0,
                    "igst": 0.0,
                    "total_tax": 108.0,
                }
            },
            "record_count": 3,
            "invalid_gstin_records": 0,
            "normalized_records": [],
        }

        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "hsn_summary.csv"
            write_output(result, out_path, "csv", "hsn")
            with out_path.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["hsn_code"], "1001")
        self.assertEqual(rows[0]["invoices"], "3")


if __name__ == "__main__":
    unittest.main()
