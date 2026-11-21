import sqlite3
import os
from contextlib import contextmanager
from config import Config

def get_db_path(custom_path=None):
    """Return the active SQLite database path."""
    return custom_path or Config.DATABASE_PATH

@contextmanager
def get_db_connection(custom_path=None):
    """Context manager for SQLite database connection with row factory and foreign keys."""
    db_path = get_db_path(custom_path)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()

def query_db(query, args=(), one=False, commit=False, custom_path=None):
    """
    Execute a parameterized SQL query safely.
    Returns:
      - single Row if one=True
      - list of Rows if one=False
      - lastrowid if commit=True and it was an INSERT
      - rowcount if commit=True and it was an UPDATE/DELETE
    """
    with get_db_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        if commit:
            conn.commit()
            if query.strip().upper().startswith("INSERT"):
                return cursor.lastrowid
            return cursor.rowcount
        rv = cursor.fetchall()
        return (rv[0] if rv else None) if one else rv

def init_db(custom_path=None):
    """Initialize database tables, schema, and indexes."""
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        roll_number TEXT UNIQUE NOT NULL,
        email TEXT,
        role TEXT NOT NULL CHECK(role IN ('student', 'warden', 'guard')),
        program TEXT,
        department TEXT,
        hostel TEXT,
        room TEXT,
        avatar TEXT,
        password_hash TEXT NOT NULL,
        gate_name TEXT,
        created_at TEXT DEFAULT (datetime('now', '+5 hours', '30 minutes'))
    );

    CREATE TABLE IF NOT EXISTS outpasses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pass_code TEXT UNIQUE NOT NULL,
        student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        destination TEXT NOT NULL,
        purpose TEXT NOT NULL,
        departure_date TEXT NOT NULL,
        departure_time TEXT NOT NULL,
        planned_exit_datetime TEXT NOT NULL,
        expected_return_datetime TEXT NOT NULL,
        declaration_agreed INTEGER DEFAULT 1 CHECK(declaration_agreed IN (0, 1)),
        status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED', 'OUTSIDE', 'COMPLETED', 'CANCELLED')),
        warden_id INTEGER REFERENCES users(id),
        rejection_reason TEXT,
        approved_at TEXT,
        verification_token TEXT UNIQUE,
        created_at TEXT DEFAULT (datetime('now', '+5 hours', '30 minutes'))
    );

    CREATE TABLE IF NOT EXISTS gate_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outpass_id INTEGER NOT NULL REFERENCES outpasses(id) ON DELETE CASCADE,
        student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        guard_id INTEGER NOT NULL REFERENCES users(id),
        gate_name TEXT NOT NULL,
        movement_type TEXT NOT NULL CHECK(movement_type IN ('EXIT', 'ENTRY')),
        timestamp TEXT NOT NULL,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        category TEXT DEFAULT 'info' CHECK(category IN ('info', 'success', 'warning', 'danger')),
        link TEXT,
        is_read INTEGER DEFAULT 0 CHECK(is_read IN (0, 1)),
        created_at TEXT DEFAULT (datetime('now', '+5 hours', '30 minutes'))
    );

    -- Performance indexes
    CREATE INDEX IF NOT EXISTS idx_users_roll ON users(roll_number);
    CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
    CREATE INDEX IF NOT EXISTS idx_outpasses_student ON outpasses(student_id);
    CREATE INDEX IF NOT EXISTS idx_outpasses_status ON outpasses(status);
    CREATE INDEX IF NOT EXISTS idx_outpasses_token ON outpasses(verification_token);
    CREATE INDEX IF NOT EXISTS idx_outpasses_code ON outpasses(pass_code);
    CREATE INDEX IF NOT EXISTS idx_gate_logs_outpass ON gate_logs(outpass_id);
    CREATE INDEX IF NOT EXISTS idx_gate_logs_gate ON gate_logs(gate_name);
    CREATE INDEX IF NOT EXISTS idx_gate_logs_timestamp ON gate_logs(timestamp);
    CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);
    """
    with get_db_connection(custom_path) as conn:
        conn.executescript(schema)
        conn.commit()
