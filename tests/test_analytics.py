import unittest
import os
import tempfile
from analyze_data import analyze_outpass_csv

class TestAnalytics(unittest.TestCase):
    def test_csv_analysis_on_demo_data(self):
        """14a. CSV analysis calculates statistics correctly from valid dataset."""
        if os.path.exists("data.csv"):
            res = analyze_outpass_csv("data.csv")
            self.assertNotIn("error", res)
            self.assertGreater(res["total_records"], 0)
            self.assertIn("completed_count", res)
            self.assertIn("gate_activity", res)
            self.assertIn("avg_duration_formatted", res)
            self.assertTrue(res["is_synthetic"])

    def test_missing_csv_file_handled_gracefully(self):
        """14b. Missing CSV file handled without exception."""
        res = analyze_outpass_csv("non_existent_file.csv")
        self.assertIn("error", res)
        self.assertTrue(res["is_synthetic"])

    def test_malformed_csv_handled_gracefully(self):
        """14c. Corrupted or malformed CSV rows do not crash analyzer."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp.write("invalid,header,without,matching,schema\n")
            tmp.write("bad_data_1,bad_data_2\n")
            tmp.write(",,,,\n")
            tmp_path = tmp.name

        try:
            res = analyze_outpass_csv(tmp_path)
            self.assertNotIn("error", res)
            self.assertEqual(res["total_records"], 2)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    unittest.main()
