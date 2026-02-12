import json
import tempfile
import unittest
from pathlib import Path

from gst_data_extractor import is_valid_gstin, read_input, summarize


class TestGSTExtractor(unittest.TestCase):
    def test_gstin_validation(self):
        self.assertTrue(is_valid_gstin("29ABCDE1234F1Z5"))
        self.assertFalse(is_valid_gstin("INVALIDGST"))

    def test_summary_json_input(self):
        sample = [
            {
                "invoice_id": "INV-1",
                "invoice_date": "2025-01-05",
                "seller_gstin": "29ABCDE1234F1Z5",
                "buyer_gstin": "27PQRSX5678L1Z2",
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


if __name__ == "__main__":
    unittest.main()
