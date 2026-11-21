import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base application configuration."""
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-gatepass-secret-key-sde1-assignment-2026")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "gatepass.db"))
    
    # Campus curfew policy (10:00 PM IST)
    CURFEW_HOUR = int(os.environ.get("DEFAULT_CURFEW_HOUR", 22))
    CURFEW_MINUTE = int(os.environ.get("DEFAULT_CURFEW_MINUTE", 0))
    
    # Timezone: IST (UTC +05:30)
    IST_OFFSET = timedelta(hours=5, minutes=30)
    IST_TZ = timezone(IST_OFFSET, name="IST")
    
    # Max upload size
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB
    
    # Available campus gates
    CAMPUS_GATES = ["Gate 1", "Gate 2", "Gate 3", "Gate 4"]
    
    # User roles
    ROLE_STUDENT = "student"
    ROLE_WARDEN = "warden"
    ROLE_GUARD = "guard"
    
    # Outpass statuses
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_OUTSIDE = "OUTSIDE"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    
    # Movement types
    MOVEMENT_EXIT = "EXIT"
    MOVEMENT_ENTRY = "ENTRY"

class TestConfig(Config):
    """Testing configuration using an in-memory or test database."""
    TESTING = True
    DATABASE_PATH = os.path.join(BASE_DIR, "test_gatepass.db")
    SECRET_KEY = "test-secret-key"
