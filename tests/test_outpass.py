import unittest
import os
import tempfile
from werkzeug.security import generate_password_hash
from app import create_app
from config import TestConfig
from database import init_db
from models import (
    create_user,
    create_outpass,
    get_outpass_by_id,
    approve_outpass,
    reject_outpass,
    record_gate_exit
)

PRECOMPUTED_HASH = generate_password_hash("pass")

class TestOutpassWorkflow(unittest.TestCase):
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
        self.guard_id = create_user(
            name="Guard 1", roll_number="guard1", password_hash=PRECOMPUTED_HASH,
            role="guard", gate_name="Gate 1", custom_path=self.db_path
        )

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_student_can_submit_outpass(self):
        """3. Student can submit an outpass request."""
        outpass_id, pass_code = create_outpass(
            student_id=self.student_id,
            destination="Civil Lines",
            purpose="Purchasing stationery books",
            departure_date="2026-11-21",
            departure_time="18:30",
            planned_exit_dt="2026-11-21 18:30:00",
            expected_return_dt="2026-11-21 21:30:00",
            declaration_agreed=1,
            custom_path=self.db_path
        )
        self.assertIsNotNone(outpass_id)
        self.assertTrue(pass_code.startswith("GP-"))

        p = get_outpass_by_id(outpass_id, custom_path=self.db_path)
        self.assertEqual(p["status"], "PENDING")
        self.assertEqual(p["destination"], "Civil Lines")
        self.assertIsNone(p["verification_token"])  # No QR token before approval

    def test_warden_can_approve_request_and_generates_token(self):
        """4 & 6. Warden can approve a request; generates unique verification QR token."""
        outpass_id, _ = create_outpass(
            student_id=self.student_id, destination="Library", purpose="Research",
            departure_date="2026-11-21", departure_time="18:00",
            planned_exit_dt="2026-11-21 18:00:00", expected_return_dt="2026-11-21 21:00:00",
            declaration_agreed=1, custom_path=self.db_path
        )

        ok, msg = approve_outpass(outpass_id, self.warden_id, custom_path=self.db_path)
        self.assertTrue(ok)

        approved_pass = get_outpass_by_id(outpass_id, custom_path=self.db_path)
        self.assertEqual(approved_pass["status"], "APPROVED")
        self.assertIsNotNone(approved_pass["approved_at"])
        self.assertIsNotNone(approved_pass["verification_token"])
        self.assertEqual(len(approved_pass["verification_token"]), 32) # 16-byte hex
        self.assertIsNotNone(approved_pass["qr_code_image"])

    def test_rejected_request_cannot_be_used_at_gate(self):
        """5. Rejected requests cannot be used at a gate to exit."""
        outpass_id, _ = create_outpass(
            student_id=self.student_id, destination="Out of Station", purpose="Trip",
            departure_date="2026-11-21", departure_time="19:00",
            planned_exit_dt="2026-11-21 19:00:00", expected_return_dt="2026-11-21 23:30:00",
            declaration_agreed=1, custom_path=self.db_path
        )

        ok_rej, _ = reject_outpass(outpass_id, self.warden_id, reason="Night travel not permitted", custom_path=self.db_path)
        self.assertTrue(ok_rej)

        p = get_outpass_by_id(outpass_id, custom_path=self.db_path)
        self.assertEqual(p["status"], "REJECTED")
        self.assertEqual(p["rejection_reason"], "Night travel not permitted")

        # Guard tries to record exit on rejected pass
        ok_exit, exit_msg = record_gate_exit(
            outpass_id=outpass_id, guard_id=self.guard_id, gate_name="Gate 1",
            custom_path=self.db_path
        )
        self.assertFalse(ok_exit)
        self.assertIn("REJECTED", exit_msg)

if __name__ == "__main__":
    unittest.main()
