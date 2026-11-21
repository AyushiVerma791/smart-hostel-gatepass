import unittest
import os
import tempfile
from werkzeug.security import generate_password_hash
from app import create_app
from config import TestConfig
from database import init_db
from models import create_user, verify_user_login

PRECOMPUTED_HASH = generate_password_hash("studentpass")
PRECOMPUTED_WARDEN_HASH = generate_password_hash("wardenpass")
PRECOMPUTED_GUARD_HASH = generate_password_hash("guardpass")

class TestAuthentication(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        
        class CustomTestConfig(TestConfig):
            DATABASE_PATH = self.db_path
            TESTING = True
            SECRET_KEY = "test-secret"
            
        self.app = create_app(CustomTestConfig)
        self.client = self.app.test_client()
        init_db(self.db_path)

        # Create demo accounts
        self.student_id = create_user(
            name="Test Student", roll_number="TEST2025001", password_hash=PRECOMPUTED_HASH,
            role="student", program="B.Tech", department="Electrical Engineering", hostel="Girls Hostel 1",
            room="GH1-101", custom_path=self.db_path
        )
        self.warden_id = create_user(
            name="Test Warden", roll_number="warden", password_hash=PRECOMPUTED_WARDEN_HASH,
            role="warden", hostel="Administration", custom_path=self.db_path
        )
        self.guard_id = create_user(
            name="Test Guard", roll_number="guard1", password_hash=PRECOMPUTED_GUARD_HASH,
            role="guard", gate_name="Gate 1", custom_path=self.db_path
        )

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_student_login_success(self):
        """1. Student login works with valid credentials."""
        user = verify_user_login("TEST2025001", "studentpass", custom_path=self.db_path)
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "student")
        self.assertEqual(user["roll_number"], "TEST2025001")

    def test_invalid_password_rejected(self):
        """Invalid credentials fail authentication."""
        user = verify_user_login("TEST2025001", "wrongpassword", custom_path=self.db_path)
        self.assertIsNone(user)

    def test_unauthorized_role_access_blocked(self):
        """2. Unauthorized role access is blocked: student cannot access warden dashboard."""
        with self.client as c:
            # Login as student
            with c.session_transaction() as sess:
                sess["user_id"] = self.student_id
                sess["role"] = "student"
                sess["name"] = "Test Student"

            # Try accessing warden dashboard
            resp = c.get("/warden/dashboard", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Unauthorized", resp.data)

            # Try accessing guard verify page
            resp_guard = c.get("/guard/verify", follow_redirects=True)
            self.assertEqual(resp_guard.status_code, 200)
            self.assertIn(b"Unauthorized", resp_guard.data)

    def test_unauthenticated_access_redirects_to_login(self):
        """Unauthenticated requests to protected endpoints redirect to login."""
        resp = self.client.get("/student/dashboard", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

if __name__ == "__main__":
    unittest.main()
