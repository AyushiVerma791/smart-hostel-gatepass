import unittest
import os
import tempfile
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import create_app
from config import TestConfig
from database import init_db
from models import (
    create_user,
    create_outpass,
    get_outpass_by_id,
    get_outpass_by_token,
    approve_outpass,
    record_gate_exit,
    record_gate_entry,
    evaluate_late_status
)

PRECOMPUTED_HASH = generate_password_hash("pass")

class TestGateOperations(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        
        class CustomTestConfig(TestConfig):
            DATABASE_PATH = self.db_path
            TESTING = True
            SECRET_KEY = "test-secret"
            
        self.app = create_app(CustomTestConfig)
        self.client = self.app.test_client()
        init_db(self.db_path)

        self.student_id = create_user(
            name="Demo Student", roll_number="MWC2025014", password_hash=PRECOMPUTED_HASH,
            role="student", program="M.Tech", department="Information Technology", hostel="Girls Hostel 3",
            room="GH3-204", custom_path=self.db_path
        )
        self.warden_id = create_user(
            name="Dr. Sunita Sharma", roll_number="warden", password_hash=PRECOMPUTED_HASH,
            role="warden", hostel="Admin", custom_path=self.db_path
        )
        self.guard1_id = create_user(
            name="Guard Gate 1", roll_number="guard1", password_hash=PRECOMPUTED_HASH,
            role="guard", gate_name="Gate 1", custom_path=self.db_path
        )
        self.guard3_id = create_user(
            name="Guard Gate 3", roll_number="guard3", password_hash=PRECOMPUTED_HASH,
            role="guard", gate_name="Gate 3", custom_path=self.db_path
        )

        # Create and approve an outpass
        self.outpass_id, self.pass_code = create_outpass(
            student_id=self.student_id,
            destination="Civil Lines",
            purpose="Personal shopping",
            departure_date="2026-11-21",
            departure_time="18:30",
            planned_exit_dt="2026-11-21 18:30:00",
            expected_return_dt="2026-11-21 21:30:00",
            declaration_agreed=1,
            custom_path=self.db_path
        )
        approve_outpass(self.outpass_id, self.warden_id, custom_path=self.db_path)
        self.pass_data = get_outpass_by_id(self.outpass_id, custom_path=self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_invalid_qr_token_rejected(self):
        """7. Invalid QR tokens return None / lookup failure."""
        res = get_outpass_by_token("fake-token-1234567890", custom_path=self.db_path)
        self.assertIsNone(res)

    def test_guard_can_record_exit(self):
        """8. An authenticated guard can record a student exit."""
        ok, msg = record_gate_exit(
            outpass_id=self.outpass_id,
            guard_id=self.guard1_id,
            gate_name="Gate 1",
            timestamp="2026-11-21 18:35:00",
            notes="Photo verified",
            custom_path=self.db_path
        )
        self.assertTrue(ok)
        self.assertIn("Gate 1", msg)

        updated = get_outpass_by_id(self.outpass_id, custom_path=self.db_path)
        self.assertEqual(updated["status"], "OUTSIDE")
        self.assertEqual(updated["exit_gate"], "Gate 1")
        self.assertEqual(updated["exit_time"], "2026-11-21 18:35:00")

    def test_duplicate_exit_prevented(self):
        """9. Duplicate exit is strictly prevented."""
        # First exit
        record_gate_exit(
            outpass_id=self.outpass_id, guard_id=self.guard1_id, gate_name="Gate 1",
            timestamp="2026-11-21 18:35:00", custom_path=self.db_path
        )
        # Attempt second exit
        ok_dup, dup_msg = record_gate_exit(
            outpass_id=self.outpass_id, guard_id=self.guard1_id, gate_name="Gate 1",
            timestamp="2026-11-21 18:40:00", custom_path=self.db_path
        )
        self.assertFalse(ok_dup)
        self.assertIn("Duplicate Exit Prevented", dup_msg)

    def test_multi_gate_exit_and_return(self):
        """10 & 11. Student can exit through Gate 1 and return through Gate 3; entry correctly recorded."""
        # 1. Exit through Gate 1
        record_gate_exit(
            outpass_id=self.outpass_id, guard_id=self.guard1_id, gate_name="Gate 1",
            timestamp="2026-11-21 18:35:00", custom_path=self.db_path
        )

        # 2. Return through Gate 3
        ok_entry, entry_msg = record_gate_entry(
            outpass_id=self.outpass_id, guard_id=self.guard3_id, gate_name="Gate 3",
            timestamp="2026-11-21 21:15:00", notes="Returned through sports gate",
            custom_path=self.db_path
        )
        self.assertTrue(ok_entry)
        self.assertIn("Gate 3", entry_msg)

        completed = get_outpass_by_id(self.outpass_id, custom_path=self.db_path)
        self.assertEqual(completed["status"], "COMPLETED")
        self.assertEqual(completed["exit_gate"], "Gate 1")
        self.assertEqual(completed["entry_gate"], "Gate 3")
        self.assertFalse(completed["is_late"]) # Returned at 21:15 (before 21:30 and before 22:00)

    def test_duplicate_entry_prevented(self):
        """12. Duplicate return is strictly prevented."""
        record_gate_exit(self.outpass_id, self.guard1_id, "Gate 1", "2026-11-21 18:35:00", custom_path=self.db_path)
        record_gate_entry(self.outpass_id, self.guard1_id, "Gate 1", "2026-11-21 21:10:00", custom_path=self.db_path)

        # Attempt second entry
        ok_dup, dup_msg = record_gate_entry(self.outpass_id, self.guard1_id, "Gate 1", "2026-11-21 21:15:00", custom_path=self.db_path)
        self.assertFalse(ok_dup)
        self.assertIn("Duplicate Entry Prevented", dup_msg)

    def test_late_returns_flagged_correctly(self):
        """13. Late returns are flagged correctly when past curfew (10 PM) or expected return time."""
        # Case A: Returned on time (expected 21:30, returned 21:15)
        is_late_a, min_late_a, _ = evaluate_late_status(
            expected_return_str="2026-11-21 21:30:00",
            actual_return_str="2026-11-21 21:15:00",
            current_status="COMPLETED"
        )
        self.assertFalse(is_late_a)
        self.assertEqual(min_late_a, 0)

        # Case B: Returned past expected return (expected 21:00, returned 21:45) -> 45 mins late
        is_late_b, min_late_b, reason_b = evaluate_late_status(
            expected_return_str="2026-11-21 21:00:00",
            actual_return_str="2026-11-21 21:45:00",
            current_status="COMPLETED"
        )
        self.assertTrue(is_late_b)
        self.assertEqual(min_late_b, 45)

        # Case C: Returned past 10 PM curfew (expected 21:45, returned 22:30) -> late past 10 PM
        is_late_c, min_late_c, reason_c = evaluate_late_status(
            expected_return_str="2026-11-21 21:45:00",
            actual_return_str="2026-11-21 22:30:00",
            current_status="COMPLETED"
        )
        self.assertTrue(is_late_c)
        self.assertEqual(min_late_c, 45) # 45 minutes past expected return
        self.assertIn("10 PM Curfew", reason_c)

if __name__ == "__main__":
    unittest.main()
