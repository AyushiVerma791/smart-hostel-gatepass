import io
import base64
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
from config import Config
from database import query_db, get_db_connection

# -------------------------------------------------------------
# Date & Time Utilities (IST: Asia/Kolkata, UTC +05:30)
# -------------------------------------------------------------

def get_now_ist():
    """Return the current datetime in Indian Standard Time (IST) as a datetime object."""
    return datetime.now(Config.IST_TZ)

def get_now_ist_str():
    """Return the current IST datetime as an ISO-like formatted string 'YYYY-MM-DD HH:MM:SS'."""
    return get_now_ist().strftime("%Y-%m-%d %H:%M:%S")

def parse_datetime(dt_str):
    """Parse a datetime string in 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DDTHH:MM'."""
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None

def format_ist_display(dt_str):
    """Format stored datetime into friendly string: '21 Nov 2026, 06:30 PM IST'."""
    dt = parse_datetime(dt_str)
    if not dt:
        return dt_str or "-"
    return dt.strftime("%d %b %Y, %I:%M %p IST")

def format_time_only(dt_str):
    """Format stored datetime into friendly time: '06:30 PM'."""
    dt = parse_datetime(dt_str)
    if not dt:
        return dt_str or "-"
    return dt.strftime("%I:%M %p")

def evaluate_late_status(expected_return_str, actual_return_str=None, current_status="OUTSIDE"):
    """
    Evaluate if an outpass is or was late.
    Returns:
      is_late (bool)
      minutes_late (int)
      reason (str)
    
    A student is considered late if:
      1. Campus curfew (10:00 PM / 22:00) on the date of departure has passed while student is outside or returned after it.
      2. OR student returned (or is currently outside) past their approved expected_return_datetime.
    """
    expected_dt = parse_datetime(expected_return_str)
    if not expected_dt:
        return False, 0, ""

    # Campus curfew for that departure date
    curfew_dt = expected_dt.replace(hour=Config.CURFEW_HOUR, minute=Config.CURFEW_MINUTE, second=0)
    # The effective deadline is the earlier of expected return or campus curfew (usually 10 PM)
    effective_deadline = min(expected_dt, curfew_dt) if expected_dt.time() > curfew_dt.time() else expected_dt

    if actual_return_str:
        # Pass has completed return
        return_dt = parse_datetime(actual_return_str)
        if return_dt and return_dt > effective_deadline:
            diff = return_dt - effective_deadline
            minutes = int(diff.total_seconds() // 60)
            if minutes > 0:
                reason = "Past 10 PM Curfew" if return_dt > curfew_dt else "Past Approved Return Time"
                return True, minutes, reason
        return False, 0, ""

    elif current_status == Config.STATUS_OUTSIDE:
        # Student is currently outside - compare with current IST time
        now = get_now_ist().replace(tzinfo=None)
        if now > effective_deadline:
            diff = now - effective_deadline
            minutes = int(diff.total_seconds() // 60)
            if minutes > 0:
                reason = "Currently Overdue (Past 10 PM Curfew)" if now > curfew_dt else "Currently Overdue (Past Expected Return)"
                return True, minutes, reason

    return False, 0, ""

# -------------------------------------------------------------
# User Model Operations
# -------------------------------------------------------------

def get_user_by_id(user_id, custom_path=None):
    """Retrieve user dictionary by ID."""
    row = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True, custom_path=custom_path)
    return dict(row) if row else None

def get_user_by_roll_number(roll_number, custom_path=None):
    """Retrieve user dictionary by roll number or username."""
    row = query_db("SELECT * FROM users WHERE LOWER(roll_number) = LOWER(?)", (roll_number.strip(),), one=True, custom_path=custom_path)
    return dict(row) if row else None

def create_user(name, roll_number, password=None, role="student", program=None, department=None,
                hostel=None, room=None, avatar=None, gate_name=None, email=None, custom_path=None, password_hash=None):
    """Create a new user with hashed password."""
    if not password_hash and password:
        password_hash = generate_password_hash(password)
    user_id = query_db(
        """
        INSERT INTO users (name, roll_number, email, role, program, department, hostel, room, avatar, password_hash, gate_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name.strip(), roll_number.strip().upper(), email, role, program, department, hostel, room, avatar, password_hash, gate_name),
        commit=True,
        custom_path=custom_path
    )
    return user_id

def verify_user_login(roll_or_user, password, custom_path=None):
    """Authenticate a user by roll number/username and password."""
    user = get_user_by_roll_number(roll_or_user, custom_path=custom_path)
    if not user:
        return None
    if check_password_hash(user["password_hash"], password):
        return user
    return None

def get_all_students(search=None, program=None, custom_path=None):
    """List student accounts with optional search filters and outpass statistics."""
    query = """
        SELECT u.*, 
               (SELECT COUNT(*) FROM outpasses WHERE student_id = u.id) AS total_outpasses,
               (SELECT status FROM outpasses WHERE student_id = u.id ORDER BY id DESC LIMIT 1) AS latest_status
        FROM users u
        WHERE u.role = 'student'
    """
    params = []
    if search:
        query += " AND (LOWER(u.name) LIKE LOWER(?) OR LOWER(u.roll_number) LIKE LOWER(?) OR LOWER(u.room) LIKE LOWER(?))"
        term = f"%{search.strip()}%"
        params.extend([term, term, term])
    if program:
        query += " AND u.program = ?"
        params.append(program)
    query += " ORDER BY u.roll_number ASC"
    rows = query_db(query, tuple(params), custom_path=custom_path)
    return [dict(r) for r in rows]

# -------------------------------------------------------------
# Outpass Model Operations
# -------------------------------------------------------------

def generate_pass_code(custom_path=None):
    """Generate a clean sequential outpass code like GP-2026-0001."""
    row = query_db("SELECT COUNT(*) AS cnt FROM outpasses", one=True, custom_path=custom_path)
    count = (row["cnt"] if row else 0) + 1
    current_year = get_now_ist().year
    return f"GP-{current_year}-{count:04d}"

def generate_verification_token():
    """Generate a secure, random verification token for QR code encoding."""
    return secrets.token_hex(16)

def generate_qr_code_base64(token):
    """
    Generate an in-memory QR code encoding ONLY the verification token.
    Returns a data URI string: 'data:image/png;base64,...'
    Safe: does not embed student personal information or passwords.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0a2540", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def create_outpass(student_id, destination, purpose, departure_date, departure_time,
                   planned_exit_dt, expected_return_dt, declaration_agreed=1, custom_path=None):
    """Create a new pending outpass application by a student."""
    pass_code = generate_pass_code(custom_path=custom_path)
    outpass_id = query_db(
        """
        INSERT INTO outpasses (
            pass_code, student_id, destination, purpose, departure_date,
            departure_time, planned_exit_datetime, expected_return_datetime,
            declaration_agreed, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
        """,
        (pass_code, student_id, destination.strip(), purpose.strip(), departure_date,
         departure_time, planned_exit_dt, expected_return_dt, declaration_agreed),
        commit=True,
        custom_path=custom_path
    )
    
    # Notify student
    create_notification(
        user_id=student_id,
        title="Outpass Application Submitted",
        message=f"Your outpass application #{pass_code} to '{destination}' has been submitted for Warden review.",
        category="info",
        link=f"/student/pass/{outpass_id}",
        custom_path=custom_path
    )
    
    # Notify all wardens
    wardens = query_db("SELECT id FROM users WHERE role = 'warden'", custom_path=custom_path)
    student = get_user_by_id(student_id, custom_path=custom_path)
    student_label = f"{student['name']} ({student['roll_number']})" if student else "A student"
    for w in wardens:
        create_notification(
            user_id=w["id"],
            title="New Outpass Request",
            message=f"{student_label} requested an outpass to '{destination}' for {departure_date}.",
            category="info",
            link="/warden/approvals",
            custom_path=custom_path
        )
        
    return outpass_id, pass_code

def get_outpass_by_id(outpass_id, custom_path=None):
    """Retrieve full outpass record with student details and logs."""
    row = query_db(
        """
        SELECT o.*, 
               u.name AS student_name, u.roll_number, u.program, u.department, 
               u.hostel, u.room, u.avatar, u.email AS student_email,
               w.name AS warden_name
        FROM outpasses o
        JOIN users u ON o.student_id = u.id
        LEFT JOIN users w ON o.warden_id = w.id
        WHERE o.id = ?
        """,
        (outpass_id,),
        one=True,
        custom_path=custom_path
    )
    if not row:
        return None
    data = dict(row)
    
    # Attach exit and entry logs if any
    logs = query_db(
        """
        SELECT gl.*, g.name AS guard_name
        FROM gate_logs gl
        JOIN users g ON gl.guard_id = g.id
        WHERE gl.outpass_id = ?
        ORDER BY gl.id ASC
        """,
        (outpass_id,),
        custom_path=custom_path
    )
    data["logs"] = [dict(l) for l in logs]
    
    # Populate exit/entry details for quick access
    exit_log = next((l for l in data["logs"] if l["movement_type"] == Config.MOVEMENT_EXIT), None)
    entry_log = next((l for l in data["logs"] if l["movement_type"] == Config.MOVEMENT_ENTRY), None)
    
    data["exit_time"] = exit_log["timestamp"] if exit_log else None
    data["exit_gate"] = exit_log["gate_name"] if exit_log else None
    data["entry_time"] = entry_log["timestamp"] if entry_log else None
    data["entry_gate"] = entry_log["gate_name"] if entry_log else None
    
    # Lateness check
    is_late, min_late, reason = evaluate_late_status(
        data["expected_return_datetime"],
        actual_return_str=data["entry_time"],
        current_status=data["status"]
    )
    data["is_late"] = is_late
    data["minutes_late"] = min_late
    data["late_reason"] = reason

    # Generate QR data uri if token exists
    if data.get("verification_token"):
        data["qr_code_image"] = generate_qr_code_base64(data["verification_token"])
    else:
        data["qr_code_image"] = None

    return data

def get_outpass_by_token(token, custom_path=None):
    """Retrieve outpass by verification token (for guard QR scan)."""
    if not token:
        return None
    row = query_db("SELECT id FROM outpasses WHERE verification_token = ?", (token.strip(),), one=True, custom_path=custom_path)
    if not row:
        return None
    return get_outpass_by_id(row["id"], custom_path=custom_path)

def get_outpass_by_code(pass_code, custom_path=None):
    """Retrieve outpass by human-readable pass code (for manual guard fallback)."""
    if not pass_code:
        return None
    row = query_db("SELECT id FROM outpasses WHERE LOWER(pass_code) = LOWER(?)", (pass_code.strip(),), one=True, custom_path=custom_path)
    if not row:
        return None
    return get_outpass_by_id(row["id"], custom_path=custom_path)

def get_student_outpasses(student_id, custom_path=None):
    """Retrieve all outpasses submitted by a specific student."""
    rows = query_db(
        """
        SELECT o.*, 
               (SELECT timestamp FROM gate_logs WHERE outpass_id = o.id AND movement_type = 'EXIT' LIMIT 1) AS exit_time,
               (SELECT gate_name FROM gate_logs WHERE outpass_id = o.id AND movement_type = 'EXIT' LIMIT 1) AS exit_gate,
               (SELECT timestamp FROM gate_logs WHERE outpass_id = o.id AND movement_type = 'ENTRY' LIMIT 1) AS entry_time,
               (SELECT gate_name FROM gate_logs WHERE outpass_id = o.id AND movement_type = 'ENTRY' LIMIT 1) AS entry_gate
        FROM outpasses o
        WHERE o.student_id = ?
        ORDER BY o.id DESC
        """,
        (student_id,),
        custom_path=custom_path
    )
    result = []
    for r in rows:
        d = dict(r)
        is_late, min_late, reason = evaluate_late_status(
            d["expected_return_datetime"],
            actual_return_str=d.get("entry_time"),
            current_status=d["status"]
        )
        d["is_late"] = is_late
        d["minutes_late"] = min_late
        d["late_reason"] = reason
        result.append(d)
    return result

def approve_outpass(outpass_id, warden_id, custom_path=None):
    """Warden approves outpass: generates verification token, records timestamp and notifies student."""
    pass_data = get_outpass_by_id(outpass_id, custom_path=custom_path)
    if not pass_data or pass_data["status"] != Config.STATUS_PENDING:
        return False, "Outpass is not in pending status."
        
    token = generate_verification_token()
    approved_at = get_now_ist_str()
    
    query_db(
        """
        UPDATE outpasses 
        SET status = 'APPROVED', warden_id = ?, approved_at = ?, verification_token = ?, rejection_reason = NULL
        WHERE id = ?
        """,
        (warden_id, approved_at, token, outpass_id),
        commit=True,
        custom_path=custom_path
    )
    
    create_notification(
        user_id=pass_data["student_id"],
        title="Outpass Approved!",
        message=f"Your outpass #{pass_data['pass_code']} to '{pass_data['destination']}' has been approved. Your digital QR pass is now ready.",
        category="success",
        link=f"/student/pass/{outpass_id}",
        custom_path=custom_path
    )
    return True, "Outpass approved successfully."

def reject_outpass(outpass_id, warden_id, reason="Application does not meet hostel policy", custom_path=None):
    """Warden rejects outpass: stores reason and notifies student."""
    pass_data = get_outpass_by_id(outpass_id, custom_path=custom_path)
    if not pass_data or pass_data["status"] != Config.STATUS_PENDING:
        return False, "Outpass is not in pending status."
        
    rejected_at = get_now_ist_str()
    clean_reason = reason.strip() if reason else "Declined by warden"
    
    query_db(
        """
        UPDATE outpasses 
        SET status = 'REJECTED', warden_id = ?, approved_at = ?, rejection_reason = ?
        WHERE id = ?
        """,
        (warden_id, rejected_at, clean_reason, outpass_id),
        commit=True,
        custom_path=custom_path
    )
    
    create_notification(
        user_id=pass_data["student_id"],
        title="Outpass Rejected",
        message=f"Your outpass #{pass_data['pass_code']} was rejected. Reason: {clean_reason}",
        category="danger",
        link=f"/student/history",
        custom_path=custom_path
    )
    return True, "Outpass rejected."

# -------------------------------------------------------------
# Gate Log & Movement Verification Operations
# -------------------------------------------------------------

def record_gate_exit(outpass_id, guard_id, gate_name, timestamp=None, notes=None, custom_path=None):
    """
    Record student EXIT at campus gate.
    Enforces workflow integrity:
      - Pass must be in APPROVED status.
      - Duplicate exit is strictly prevented.
      - Updates status to OUTSIDE.
      - Adds record to gate_logs.
      - Notifies student.
    """
    pass_data = get_outpass_by_id(outpass_id, custom_path=custom_path)
    if not pass_data:
        return False, "Pass not found."
        
    if pass_data["status"] == Config.STATUS_OUTSIDE:
        return False, f"Duplicate Exit Prevented: Student is already marked as OUTSIDE (exited at {pass_data.get('exit_gate', 'a gate')})."
        
    if pass_data["status"] == Config.STATUS_COMPLETED:
        return False, "Pass Already Completed: Student has already exited and returned."
        
    if pass_data["status"] != Config.STATUS_APPROVED:
        return False, f"Cannot record exit: Outpass status is '{pass_data['status']}', not APPROVED."
        
    # Check if an exit log already exists
    existing_exit = query_db(
        "SELECT id FROM gate_logs WHERE outpass_id = ? AND movement_type = 'EXIT'",
        (outpass_id,),
        one=True,
        custom_path=custom_path
    )
    if existing_exit:
        return False, "Duplicate Exit Prevented: An exit has already been logged for this pass."
        
    exit_time = timestamp or get_now_ist_str()
    
    with get_db_connection(custom_path) as conn:
        cursor = conn.cursor()
        # 1. Update outpass status
        cursor.execute("UPDATE outpasses SET status = 'OUTSIDE' WHERE id = ?", (outpass_id,))
        # 2. Insert gate log
        cursor.execute(
            """
            INSERT INTO gate_logs (outpass_id, student_id, guard_id, gate_name, movement_type, timestamp, notes)
            VALUES (?, ?, ?, ?, 'EXIT', ?, ?)
            """,
            (outpass_id, pass_data["student_id"], guard_id, gate_name, exit_time, notes)
        )
        conn.commit()
        
    # Notify student
    create_notification(
        user_id=pass_data["student_id"],
        title="Exit Recorded",
        message=f"Departure logged at {gate_name} at {format_time_only(exit_time)}. Please return before {format_time_only(pass_data['expected_return_datetime'])}.",
        category="info",
        link=f"/student/pass/{outpass_id}",
        custom_path=custom_path
    )
    
    return True, f"Exit successfully verified and logged at {gate_name}."

def record_gate_entry(outpass_id, guard_id, gate_name, timestamp=None, notes=None, custom_path=None):
    """
    Record student ENTRY at campus gate.
    Enforces workflow integrity:
      - Pass must be in OUTSIDE status.
      - Duplicate entry is strictly prevented.
      - Updates status to COMPLETED.
      - Adds record to gate_logs.
      - Checks lateness and sends warden alert if overdue.
      - Notifies student.
    """
    pass_data = get_outpass_by_id(outpass_id, custom_path=custom_path)
    if not pass_data:
        return False, "Pass not found."
        
    if pass_data["status"] == Config.STATUS_COMPLETED:
        return False, f"Duplicate Entry Prevented: Pass #{pass_data['pass_code']} is already completed."
        
    if pass_data["status"] != Config.STATUS_OUTSIDE:
        return False, f"Cannot record entry: Student has not exited yet (Current status: {pass_data['status']})."
        
    # Check if an entry log already exists
    existing_entry = query_db(
        "SELECT id FROM gate_logs WHERE outpass_id = ? AND movement_type = 'ENTRY'",
        (outpass_id,),
        one=True,
        custom_path=custom_path
    )
    if existing_entry:
        return False, "Duplicate Entry Prevented: An entry log already exists for this pass."
        
    entry_time = timestamp or get_now_ist_str()
    
    with get_db_connection(custom_path) as conn:
        cursor = conn.cursor()
        # 1. Update outpass status
        cursor.execute("UPDATE outpasses SET status = 'COMPLETED' WHERE id = ?", (outpass_id,))
        # 2. Insert gate log
        cursor.execute(
            """
            INSERT INTO gate_logs (outpass_id, student_id, guard_id, gate_name, movement_type, timestamp, notes)
            VALUES (?, ?, ?, ?, 'ENTRY', ?, ?)
            """,
            (outpass_id, pass_data["student_id"], guard_id, gate_name, entry_time, notes)
        )
        conn.commit()
        
    # Lateness check
    is_late, min_late, reason = evaluate_late_status(
        pass_data["expected_return_datetime"],
        actual_return_str=entry_time,
        current_status=Config.STATUS_COMPLETED
    )
    
    # Notify student
    if is_late:
        create_notification(
            user_id=pass_data["student_id"],
            title="Return Recorded (Late)",
            message=f"Return logged at {gate_name} at {format_time_only(entry_time)}. You are {min_late} minutes past the deadline ({reason}).",
            category="warning",
            link=f"/student/pass/{outpass_id}",
            custom_path=custom_path
        )
        # Notify wardens
        wardens = query_db("SELECT id FROM users WHERE role = 'warden'", custom_path=custom_path)
        for w in wardens:
            create_notification(
                user_id=w["id"],
                title="Late Return Alert",
                message=f"Student {pass_data['student_name']} ({pass_data['roll_number']}) returned {min_late}m late at {gate_name} ({reason}).",
                category="danger",
                link="/warden/movements",
                custom_path=custom_path
            )
    else:
        create_notification(
            user_id=pass_data["student_id"],
            title="Return Recorded (On Time)",
            message=f"Safe return logged at {gate_name} at {format_time_only(entry_time)}. Thank you!",
            category="success",
            link=f"/student/pass/{outpass_id}",
            custom_path=custom_path
        )
        
    return True, f"Entry successfully verified and logged at {gate_name}."

def get_recent_gate_logs(gate_name=None, limit=20, custom_path=None):
    """Retrieve recent gate movements, optionally filtered by gate."""
    query = """
        SELECT gl.*, 
               o.pass_code, o.destination,
               u.name AS student_name, u.roll_number, u.program, u.room, u.avatar,
               g.name AS guard_name
        FROM gate_logs gl
        JOIN outpasses o ON gl.outpass_id = o.id
        JOIN users u ON gl.student_id = u.id
        JOIN users g ON gl.guard_id = g.id
    """
    params = []
    if gate_name:
        query += " WHERE gl.gate_name = ?"
        params.append(gate_name)
    query += " ORDER BY gl.id DESC LIMIT ?"
    params.append(limit)
    
    rows = query_db(query, tuple(params), custom_path=custom_path)
    return [dict(r) for r in rows]

def get_all_movements(search=None, program=None, status_filter=None, date_filter=None, custom_path=None):
    """Retrieve movement overview list for Warden with search and filter capabilities."""
    query = """
        SELECT o.*, 
               u.name AS student_name, u.roll_number, u.program, u.department, u.hostel, u.room, u.avatar,
               (SELECT timestamp FROM gate_logs WHERE outpass_id = o.id AND movement_type = 'EXIT' LIMIT 1) AS exit_time,
               (SELECT gate_name FROM gate_logs WHERE outpass_id = o.id AND movement_type = 'EXIT' LIMIT 1) AS exit_gate,
               (SELECT timestamp FROM gate_logs WHERE outpass_id = o.id AND movement_type = 'ENTRY' LIMIT 1) AS entry_time,
               (SELECT gate_name FROM gate_logs WHERE outpass_id = o.id AND movement_type = 'ENTRY' LIMIT 1) AS entry_gate
        FROM outpasses o
        JOIN users u ON o.student_id = u.id
        WHERE o.status IN ('APPROVED', 'OUTSIDE', 'COMPLETED')
    """
    params = []
    if search:
        query += " AND (LOWER(u.name) LIKE LOWER(?) OR LOWER(u.roll_number) LIKE LOWER(?) OR LOWER(u.room) LIKE LOWER(?))"
        term = f"%{search.strip()}%"
        params.extend([term, term, term])
    if program:
        query += " AND u.program = ?"
        params.append(program)
    if status_filter:
        query += " AND o.status = ?"
        params.append(status_filter)
    if date_filter:
        query += " AND o.departure_date = ?"
        params.append(date_filter)
        
    query += " ORDER BY o.id DESC"
    rows = query_db(query, tuple(params), custom_path=custom_path)
    
    result = []
    for r in rows:
        d = dict(r)
        is_late, min_late, reason = evaluate_late_status(
            d["expected_return_datetime"],
            actual_return_str=d.get("entry_time"),
            current_status=d["status"]
        )
        d["is_late"] = is_late
        d["minutes_late"] = min_late
        d["late_reason"] = reason
        result.append(d)
    return result

def get_warden_kpis(custom_path=None):
    """Calculate key performance metrics for the Warden Dashboard."""
    pending = query_db("SELECT COUNT(*) AS cnt FROM outpasses WHERE status = 'PENDING'", one=True, custom_path=custom_path)["cnt"]
    approved = query_db("SELECT COUNT(*) AS cnt FROM outpasses WHERE status = 'APPROVED'", one=True, custom_path=custom_path)["cnt"]
    outside_passes = query_db(
        """
        SELECT o.*, u.name AS student_name, u.roll_number, u.program, u.room, u.avatar,
               (SELECT timestamp FROM gate_logs WHERE outpass_id = o.id AND movement_type = 'EXIT' LIMIT 1) AS exit_time,
               (SELECT gate_name FROM gate_logs WHERE outpass_id = o.id AND movement_type = 'EXIT' LIMIT 1) AS exit_gate
        FROM outpasses o
        JOIN users u ON o.student_id = u.id
        WHERE o.status = 'OUTSIDE'
        ORDER BY o.id DESC
        """,
        custom_path=custom_path
    )
    
    outside_list = []
    overdue_count = 0
    for r in outside_passes:
        d = dict(r)
        is_late, min_late, reason = evaluate_late_status(
            d["expected_return_datetime"],
            current_status="OUTSIDE"
        )
        d["is_late"] = is_late
        d["minutes_late"] = min_late
        d["late_reason"] = reason
        if is_late:
            overdue_count += 1
        outside_list.append(d)
        
    # All completed passes that were late
    completed_passes = query_db(
        """
        SELECT o.expected_return_datetime, 
               (SELECT timestamp FROM gate_logs WHERE outpass_id = o.id AND movement_type = 'ENTRY' LIMIT 1) AS entry_time
        FROM outpasses o
        WHERE o.status = 'COMPLETED'
        """,
        custom_path=custom_path
    )
    returned_late_count = 0
    for cp in completed_passes:
        is_late, _, _ = evaluate_late_status(cp["expected_return_datetime"], actual_return_str=cp["entry_time"], current_status="COMPLETED")
        if is_late:
            returned_late_count += 1

    return {
        "pending_count": pending,
        "approved_count": approved,
        "outside_count": len(outside_list),
        "outside_students": outside_list,
        "overdue_outside_count": overdue_count,
        "returned_late_count": returned_late_count,
        "total_late_incidents": overdue_count + returned_late_count
    }

# -------------------------------------------------------------
# Notification Model Operations
# -------------------------------------------------------------

def create_notification(user_id, title, message, category="info", link=None, custom_path=None):
    """Store an in-app notification in SQLite."""
    now_ist = get_now_ist_str()
    query_db(
        """
        INSERT INTO notifications (user_id, title, message, category, link, is_read, created_at)
        VALUES (?, ?, ?, ?, ?, 0, ?)
        """,
        (user_id, title.strip(), message.strip(), category, link, now_ist),
        commit=True,
        custom_path=custom_path
    )

def get_user_notifications(user_id, unread_only=False, limit=25, custom_path=None):
    """Retrieve user notifications."""
    query = "SELECT * FROM notifications WHERE user_id = ?"
    params = [user_id]
    if unread_only:
        query += " AND is_read = 0"
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = query_db(query, tuple(params), custom_path=custom_path)
    return [dict(r) for r in rows]

def get_unread_notification_count(user_id, custom_path=None):
    """Count unread notifications for bell badge."""
    row = query_db("SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,), one=True, custom_path=custom_path)
    return row["cnt"] if row else 0

def mark_notification_as_read(notification_id, user_id, custom_path=None):
    """Mark a specific notification as read."""
    query_db("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notification_id, user_id), commit=True, custom_path=custom_path)

def mark_all_notifications_as_read(user_id, custom_path=None):
    """Mark all notifications as read for a user."""
    query_db("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,), commit=True, custom_path=custom_path)
