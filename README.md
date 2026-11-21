# GatePass — Smart Girls' Hostel Outpass Management System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![Bootstrap](https://img.shields.io/badge/Frontend-Bootstrap%205-purple.svg)](https://getbootstrap.com/)
[![Tests](https://img.shields.io/badge/Tests-16%20Passed-success.svg)](tests/)

> **24-Hour SDE-1 Take-Home Assignment Deliverable**  
> A full-stack, mobile-responsive web application modernizing residential hostel outpasses with cryptographic QR verification, role-based workflows, multi-gate logging, in-app alerts, and late-return audit intelligence.

---

## 1. Project Title
**GatePass — Smart Girls' Hostel Outpass Management System**

---

## 2. Problem Statement
In collegiate residential campuses, female students residing in hostels must obtain physical paper outpasses from the warden to leave campus premises after designated evening hours (typically after 6:00 PM).

The legacy paper workflow introduces critical operational failures:
1. **Limited Office Windows:** Students must queue at the warden’s office during a restrictive 2–3-hour daily window, clashing with laboratory sessions, library study, and lectures.
2. **Fragile Physical Artifacts:** Paper outpasses are easily torn, misplaced, soaked in rain, or forgotten in hostel rooms.
3. **Manual Entry & Exit Errors:** Security guards manually record student arrival and departure in physical paper logbooks, leading to illegible names, missed entries, and clerical mistakes.
4. **Multi-Gate Coordination Breakdown:** Campus layouts feature peripheral gates (Gate 1, Gate 2, Gate 3, Gate 4). A student leaving through Gate 1 and returning via Gate 3 produces disjointed paper logs, making it nearly impossible to reconcile student whereabouts.
5. **No Real-Time Visibility:** The hostel warden has no instant visibility into how many students are currently off-campus or who has failed to return prior to the 10:00 PM campus curfew.
6. **Zero Student Feedback:** Students remain anxious with no visibility into whether their submitted application was approved or rejected until they physically visit the office.

---

## 3. Proposed Solution
**GatePass** is a centralized, lightweight web application designed as a simple Flask monolith. It eliminates physical paper slips by offering:
- **Role-Based Portals:** Dedicated web interfaces tailored for **Students**, the **Hostel Warden**, and **Security Guards**.
- **Cryptographic QR Verification:** Instant QR generation on approval containing a hard-to-guess token (no sensitive personal data embedded).
- **Physical Photo Comparison:** High-resolution student photo and academic credentials displayed on the guard terminal for visual verification.
- **Multi-Gate Log Synchronization:** Fully supports asymmetric transit (e.g. exit through Gate 1, return through Gate 3) with automatic timestamping in Indian Standard Time (IST).
- **Automated Curfew & Late Flagging:** Flags late returns in real-time when a student exceeds their approved return time or the institutional 10:00 PM campus curfew.
- **In-App Notification Center:** Real-time feedback for students and urgent late-return alerts for wardens.

---

## 4. Main Features

### A. Student Portal
- Secure login using institutional roll number and password.
- Interactive dashboard displaying active passes, request counts, and recent movements.
- Outpass application form with departure date, departure time, expected return time, destination, and purpose.
- Digital legal declaration checkbox acknowledging campus safety rules and curfew policies.
- Real-time status tracking: `PENDING`, `APPROVED`, `OUTSIDE`, `COMPLETED`, or `REJECTED`.
- Detailed rejection remarks viewable directly if an application is declined.
- High-resolution printable/downloadable digital QR boarding pass.
- Complete historical audit log of all previous outpass records.
- In-app notification center with unread bell counter.

### B. Warden Command Console
- Comprehensive administrative dashboard with 4 real-time KPI cards:
  - Pending Approvals count
  - Active Approved passes
  - Students Currently Outside
  - Total Late/Overdue incidents
- Outpass approval inbox with student search and program filter (B.Tech, M.Tech, PhD).
- One-click approval generating cryptographically secure QR tokens and approval timestamps.
- Structured rejection modal with mandatory institutional feedback remark.
- Live "Students Currently Outside" roster showing exit gate, departure timestamp, expected return time, and overdue indicators.
- Master movement records table with multi-criteria search and filter.
- In-app alerts when students return late or remain outside past curfew.
- System analytics dashboard showing gate loads, durations, and approval metrics.

### C. Security Guard Station Console
- Distinct guard accounts permanently assigned to campus gates: **Gate 1**, **Gate 2**, **Gate 3**, and **Gate 4**.
- Built-in HTML5 QR camera scanner using `html5-qrcode` for phone and webcam scanning.
- Quick manual pass code entry fallback (e.g., entering `GP-2026-0007`).
- Full student identity card showing student photograph, roll number, department, program, hostel, and room number.
- Guard visually verifies physical student identity against displayed photo.
- Context-aware action buttons:
  - **Confirm EXIT:** Validates pass is `APPROVED`, logs timestamp, sets state to `OUTSIDE`.
  - **Confirm ENTRY:** Validates student is `OUTSIDE`, logs timestamp, sets state to `COMPLETED`.
- Strictly blocks duplicate exits, duplicate entries, unapproved passes, and expired passes.
- Displays recent timestamped activity log for that specific gate.

---

## 5. Technology Stack

| Layer | Technologies Used | Description |
|---|---|---|
| **Backend** | Python 3.10+, Flask 3.x | Lightweight, maintainable WSGI monolith |
| **Authentication** | Flask Sessions & Werkzeug | Cryptographic password hashing (`generate_password_hash`) & role RBAC |
| **Database** | SQLite3 | Normalized relational database with foreign keys & indexes |
| **Frontend** | HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons | Responsive, navy blue & white administrative SaaS UI |
| **Client Scripting** | Vanilla JavaScript (ES6) | Light polling, alert handling, dynamic QR camera scanner |
| **QR Code Generation** | Python `qrcode[pil]` | In-memory base64 PNG data-URI generator |
| **QR Code Scanning** | `html5-qrcode` 2.3.8 | Cross-platform camera scanner with manual code fallback |
| **Data Analytics** | Python `csv`, `datetime`, `collections` | Automated benchmarking & analysis module (`analyze_data.py`) |
| **Testing** | Python `unittest` | 16 automated end-to-end integration test cases |

---

## 6. System Architecture

```text
+-----------------------------------------------------------------------------------+
|                                 CLIENT BROWSERS                                   |
|   (Mobile Safari, Android Chrome, Desktop Edge/Chrome - Inter / Bootstrap 5 UI)   |
+---------------------+-----------------------+---------------------+---------------+
                      |                       |                     |
                      v                       v                     v
              +---------------+       +---------------+     +---------------+
              | Student Portal|       | Warden Console|     | Guard Terminal|
              +-------+-------+       +-------+-------+     +-------+-------+
                      |                       |                     |
                      +-----------------------+---------------------+
                                              |
                                              v  HTTP / Session Auth + CSRF
+-----------------------------------------------------------------------------------+
|                               FLASK CORE ENGINE (app.py)                          |
|  - Role-Based Access Control (@login_required, @role_required)                    |
|  - Outpass State Machine (PENDING -> APPROVED -> OUTSIDE -> COMPLETED)            |
|  - In-Memory QR Code Generator (qrcode + Pillow base64 PNG)                       |
|  - IST Timezone Engine (Asia/Kolkata + 10:00 PM Curfew Evaluator)                 |
|  - In-App Notification Dispatcher                                                 |
+-----------------------------------------------------------------------------------+
                                              |
                                              v  Parameterized SQL / PRAGMA FK
+-----------------------------------------------------------------------------------+
|                             SQLITE DATABASE (gatepass.db)                         |
|  +--------------------+  +----------------------+  +---------------------------+  |
|  |       users        |  |      outpasses       |  |         gate_logs         |  |
|  | (Students, Wardens,|  | (Pass Code, Token,   |  | (Outpass ID, Guard ID,    |  |
|  |  Guards 1-4)       |  |  Schedule, Status)   |  |  Gate 1-4, EXIT/ENTRY)    |  |
|  +--------------------+  +----------------------+  +---------------------------+  |
|                                                     +---------------------------+  |
|                                                     |       notifications       |  |
|                                                     +---------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 7. Three User Roles

### 1. Student
- Belongs to **B.Tech**, **M.Tech**, or **PhD**.
- Profile attributes: Student name, roll number, program, department, hostel, room number, profile photo / SVG avatar, email, password.
- Applies for evening outpasses, tracks approval, presents QR code at security gates, and receives notifications.
- **Security Constraint:** Cannot approve own outpasses or tamper with gate timestamps.

### 2. Warden
- Authorized administrative user (`warden`).
- Reviews pending student outpasses, approves or rejects with institutional remarks.
- Approvals trigger automatic QR token generation and notification dispatch.
- Monitors all students currently outside and receives immediate alerts for returns past the 10:00 PM curfew.

### 3. Security Guard
- Stationed at one of 4 physical gates: **Gate 1**, **Gate 2**, **Gate 3**, or **Gate 4**.
- Operates mobile camera QR scanner or enters manual pass code.
- Visually verifies student identity against displayed profile photograph.
- Explicitly confirms `EXIT` or `ENTRY` to update the central ledger.

---

## 8. Application Workflow

```text
[Step 1: Student Applies]
  Student logs in -> Submits outpass form (Destination, Purpose, Schedule) -> Agrees to declaration
         |
         v
[Step 2: Warden Reviews]
  Appears in Warden Approvals Inbox -> Warden inspects credentials -> Approves or Rejects with Remark
         |
         +----------------------------------+
         | (If Approved)                    | (If Rejected)
         v                                  v
[Step 3: QR Pass Generation]         [Application Rejected]
  - Unique Pass ID generated         - Rejection reason stored
  - Random 32-char token generated   - Student notified
  - QR Code rendered in Student App  - Cannot be used at gate
         |
         v
[Step 4: Student Departure (Exit)]
  At Gate 1, 2, 3, or 4:
  - Guard scans QR code or enters pass code
  - Guard verifies student against displayed identity photo
  - Guard clicks "Confirm EXIT"
  - Pass status becomes OUTSIDE; Departure time and Gate recorded
         |
         v
[Step 5: Student Return (Entry)]
  At any Gate (can exit Gate 1 and return via Gate 3):
  - Guard scans pass again
  - Guard clicks "Confirm ENTRY"
  - Pass status becomes COMPLETED; Arrival time and Gate recorded
         |
         v
[Step 6: Late-Return Monitoring]
  - System checks arrival time against approved expected return and 10:00 PM campus curfew
  - If returned late: Lateness minutes calculated, late badge flagged, alert dispatched to Warden
```

---

## 9. Database Overview

The application utilizes a normalized SQLite database with foreign key enforcement (`PRAGMA foreign_keys = ON;`) and indexes on high-frequency query paths.

### Schema Summary

#### `users` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique user identifier |
| `name` | TEXT | NOT NULL | User full name |
| `roll_number` | TEXT | UNIQUE NOT NULL | Roll number (students) or username (warden, guard1-4) |
| `email` | TEXT | NULLABLE | Email address |
| `role` | TEXT | NOT NULL CHECK IN ('student', 'warden', 'guard') | Role RBAC |
| `program` | TEXT | NULLABLE | B.Tech, M.Tech, or PhD (for students) |
| `department` | TEXT | NULLABLE | Department name |
| `hostel` | TEXT | NULLABLE | Hostel name (e.g. Girls Hostel 3) |
| `room` | TEXT | NULLABLE | Room number (e.g. GH3-204) |
| `avatar` | TEXT | NULLABLE | Relative path to SVG avatar / photograph |
| `password_hash` | TEXT | NOT NULL | Werkzeug scrypt/pbkdf2 hash |
| `gate_name` | TEXT | NULLABLE | Gate 1, Gate 2, Gate 3, or Gate 4 (for guards) |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | Account creation timestamp (IST) |

#### `outpasses` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Outpass ID |
| `pass_code` | TEXT | UNIQUE NOT NULL | Formatted pass ID (e.g. `GP-2026-0001`) |
| `student_id` | INTEGER | NOT NULL REFERENCES users(id) | Student who submitted application |
| `destination` | TEXT | NOT NULL | Destination of visit |
| `purpose` | TEXT | NOT NULL | Purpose of visit |
| `departure_date` | TEXT | NOT NULL | YYYY-MM-DD |
| `departure_time` | TEXT | NOT NULL | HH:MM |
| `planned_exit_datetime` | TEXT | NOT NULL | ISO datetime string |
| `expected_return_datetime` | TEXT | NOT NULL | ISO datetime string |
| `declaration_agreed` | INTEGER | DEFAULT 1 CHECK(0, 1) | Legal student consent acknowledgment |
| `status` | TEXT | NOT NULL DEFAULT 'PENDING' | PENDING, APPROVED, REJECTED, OUTSIDE, COMPLETED, CANCELLED |
| `warden_id` | INTEGER | REFERENCES users(id) | Approving warden ID |
| `rejection_reason` | TEXT | NULLABLE | Administrative reason if declined |
| `approved_at` | TEXT | NULLABLE | Timestamp of approval |
| `verification_token` | TEXT | UNIQUE NULLABLE | 32-char cryptographically secure QR token |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | Application submission timestamp |

#### `gate_logs` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Gate log record ID |
| `outpass_id` | INTEGER | NOT NULL REFERENCES outpasses(id) | Linked outpass |
| `student_id` | INTEGER | NOT NULL REFERENCES users(id) | Student passing gate |
| `guard_id` | INTEGER | NOT NULL REFERENCES users(id) | Authenticated guard confirming movement |
| `gate_name` | TEXT | NOT NULL | Gate 1, Gate 2, Gate 3, or Gate 4 |
| `movement_type` | TEXT | NOT NULL CHECK IN ('EXIT', 'ENTRY') | Movement classification |
| `timestamp` | TEXT | NOT NULL | Exact movement timestamp (IST) |
| `notes` | TEXT | NULLABLE | Guard observation remarks |

#### `notifications` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Notification ID |
| `user_id` | INTEGER | NOT NULL REFERENCES users(id) | Recipient user |
| `title` | TEXT | NOT NULL | Notification title |
| `message` | TEXT | NOT NULL | Notification message text |
| `category` | TEXT | DEFAULT 'info' | info, success, warning, danger |
| `link` | TEXT | NULLABLE | Deep link to pass or dashboard |
| `is_read` | INTEGER | DEFAULT 0 CHECK(0, 1) | Unread / read indicator |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

---

## 10. Folder Structure

```text
GatePass/
├── app.py                     # Flask application factory, routes, filters, & auth
├── config.py                  # App configuration, curfew settings, & timezone constants
├── database.py                # SQLite schema initialization, connection pool, & queries
├── models.py                  # Domain models, QR generation, lateness evaluator, & helpers
├── seed.py                    # Synthetic benchmark data & local SVG avatar generator
├── analyze_data.py            # CSV reader, statistical analyzer, & CLI report tool
├── data.csv                   # Synthetic benchmark dataset (36 simulated outpasses)
├── requirements.txt           # Python dependency specifications
├── .gitignore                 # Git ignore rules for virtualenvs, caches, & databases
├── .env.example               # Template environment configuration variables
├── README.md                  # Comprehensive technical documentation & user guide
├── research.md                # Problem analysis, existing solutions comparison, & literature notes
├── fieldwork_template.md      # Ground truth fieldwork observation template (marked incomplete)
├── reflection_template.md     # Personal reflection prompts (no AI-fabricated content)
├── ai-chats/                  # Directory for exported AI conversation logs
├── tests/                     # Automated test suite (16 tests covering all workflows)
│   ├── test_auth.py           # Authentication, passwords, & role-based route protection
│   ├── test_outpass.py        # Outpass creation, warden approvals, & QR token generation
│   ├── test_gate.py           # Guard exit/entry, duplicate protection, multi-gate, & lateness
│   └── test_analytics.py      # CSV analyzer resilience & malformed data handling
├── static/
│   ├── css/
│   │   └── style.css          # Navy blue theme, cards, badges, & responsive styles
│   ├── js/
│   │   └── main.js            # HTML5 camera scanner controller, alerts, & notification poll
│   └── avatars/               # Generated identifiable SVG student avatars (offline-ready)
└── templates/
    ├── base.html              # Core layout, navbar, notification bell, & flash messages
    ├── login.html             # Login screen with 1-click quick-fill demo buttons
    ├── notifications.html     # In-app notification center & mark-read controls
    ├── student/
    │   ├── dashboard.html     # Student metrics, active pass alert, & recent history
    │   ├── apply.html         # Outpass application form with digital declaration
    │   ├── history.html       # Filterable pass history with status badges & remarks
    │   └── pass_view.html     # Digital QR boarding card with printable styling
    ├── warden/
    │   ├── dashboard.html     # Command overview, KPI cards, & urgent requests
    │   ├── approvals.html     # Pending inbox with search & rejection remark modal
    │   ├── movements.html     # Master student movement log across all 4 gates
    │   └── analytics.html     # Visual CSV intelligence & live metrics dashboard
    └── guard/
        ├── dashboard.html     # Station console for assigned gate & today's logs
        └── verify.html        # QR scanner, manual code lookup, & verification card
```

---

## 11. Installation Instructions

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14 installed.
- Git (optional, for version control).
- Any modern web browser (Chrome, Edge, Firefox, Safari).

### Windows Setup
```powershell
# 1. Clone or navigate to the project directory
cd D:\Antigravity\Project

# 2. Create a virtual environment (optional but recommended)
python -m venv venv

# 3. Activate the virtual environment
.\venv\Scripts\Activate.ps1
# If PowerShell script execution is restricted, run:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 4. Install dependencies
pip install -r requirements.txt
```

### macOS / Linux Setup
```bash
# 1. Navigate to project directory
cd /path/to/GatePass

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 12. How to Initialize the Database
The database tables and performance indexes are automatically created on first application launch via `database.init_db()`.  
To explicitly initialize or re-initialize:
```bash
python -c "from database import init_db; init_db()"
```

---

## 13. How to Generate Demo Data
Run the synthetic data seeder:
```bash
python seed.py
```
This will:
1. Initialize the SQLite database schema.
2. Generate 32 fictional student accounts across **B.Tech**, **M.Tech**, and **PhD**.
3. Generate local SVG profile avatars for every student in `static/avatars/`.
4. Create the Chief Warden account and 4 Security Guard accounts (Gate 1 through Gate 4).
5. Generate 36 realistic simulated outpass and gate movement records (Pending, Approved, Outside, Completed on time, Completed late, and Multi-Gate transits).
6. Export the synthetic dataset to `data.csv`.

---

## 14. How to Run the Flask Server
Start the local Flask development server:
```bash
python app.py
```
You will see output similar to:
```text
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 15. Demo Login Credentials

> [!NOTE]
> For instantaneous testing, the **Login Screen includes 1-Click Quick Fill Buttons** that automatically populate credentials for any role!

| Role | Username / Roll No | Password | Description & Assignment |
|---|---|---|---|
| **Student (M.Tech)** | `MWC2025014` | `student123` | Demo Student (ECE, GH3-204) — Prompt Example |
| **Student (B.Tech)** | `IIT2025001` | `student123` | Aarohi Verma (CSE, GH1-101) |
| **Student (PhD)** | `PHD2025001` | `student123` | Dr. Arundhati Ghosh (GH3-401) |
| **Hostel Warden** | `warden` | `warden123` | Dr. Sunita Sharma (Chief Warden) |
| **Security Guard 1** | `guard1` | `guard123` | Rajesh Kumar — Assigned to **Gate 1** |
| **Security Guard 2** | `guard2` | `guard123` | Vikram Singh — Assigned to **Gate 2** |
| **Security Guard 3** | `guard3` | `guard123` | Manoj Tiwari — Assigned to **Gate 3** |
| **Security Guard 4** | `guard4` | `guard123` | Ramesh Chandra — Assigned to **Gate 4** |

---

## 16. How to Test Student, Warden, and Guard Workflows

### Complete End-to-End Test Workflow:
1. **Apply as Student:**
   - Sign in as `MWC2025014` / `student123`.
   - Click **Apply Outpass** on the navbar.
   - Enter Destination (`Hazratganj`), Departure Time (`18:30`), Expected Return (`21:30`), Purpose (`Academic reference material`).
   - Check the **Digital Declaration checkbox** and submit.
   - Your application is assigned a pass code (e.g. `GP-2026-0037`) with status `PENDING`.

2. **Approve as Warden:**
   - Click Sign Out, then sign in as `warden` / `warden123`.
   - On the Warden Dashboard, see the new pending application.
   - Click **Approvals** or the green **Approve** button.
   - The application is approved, status changes to `APPROVED`, and a cryptographic QR verification token is generated.

3. **View QR Pass as Student:**
   - Log back in as `MWC2025014`.
   - Click on the new pass to open the **Digital QR Pass**.
   - Notice the green `APPROVED &bull; READY FOR EXIT` status, student photograph, and rendered QR code. Note down the pass code (e.g. `GP-2026-0037`).

4. **Confirm Departure at Gate 1:**
   - Sign in as `guard1` / `guard123` (Assigned to **Gate 1**).
   - Go to **QR Scanner & Verify**.
   - Enter `GP-2026-0037` in the lookup box (or scan the QR code via webcam).
   - The verification card shows the student photo, name, destination, and expected return time.
   - Click **Confirm EXIT & Log Departure at Gate 1**.
   - Status updates to `OUTSIDE`. Departure timestamp is recorded at Gate 1.

5. **Confirm Multi-Gate Arrival at Gate 3:**
   - Sign out and sign in as `guard3` / `guard123` (Assigned to **Gate 3**).
   - Navigate to **QR Scanner & Verify**.
   - Enter `GP-2026-0037`.
   - The terminal recognizes the student is currently outside.
   - Click **Confirm ENTRY & Log Arrival at Gate 3**.
   - Status updates to `COMPLETED`. Multi-gate transit (Exit Gate 1 &rarr; Return Gate 3) is recorded!

6. **Verify in Warden Movements:**
   - Sign in as `warden`.
   - Open **Student Movements**.
   - Search for `MWC2025014`: View both Gate 1 exit and Gate 3 arrival logs with accurate timestamps.

---

## 17. QR Scanner Instructions & Manual Fallback

### Camera Scanner
1. On the Guard verification page (`/guard/verify`), click **Start Camera**.
2. If prompted by your browser, grant camera permissions.
3. Hold the student's digital QR pass in front of the lens.
4. On detection, `html5-qrcode` decodes the cryptographic token and automatically displays the student verification card.

### Manual Pass-Code Fallback
If the device has no camera, camera permissions are blocked, or browser security restricts video access over plain HTTP:
1. Enter the pass code directly into the input field (e.g. `GP-2026-0007`).
2. Click **Verify** or press Enter.
3. The guard console resolves the record with identical security checks and displays the visual verification card.

---

## 18. Screenshots Section
*(Placeholders for your submission recording and documentation)*

1. **Student Dashboard & Active Outpass:**  
   `docs/screenshots/01_student_dashboard.png`  
   *Displays active pass status banner, KPI cards, and quick apply button.*

2. **Digital QR Outpass Boarding Pass:**  
   `docs/screenshots/02_digital_qr_pass.png`  
   *Displays student photo, roll number, hostel room, status badge, and cryptographic QR code.*

3. **Warden Approvals & Live Outside Roster:**  
   `docs/screenshots/03_warden_approvals.png`  
   *Displays incoming requests, search filters, and one-click approve/reject modal.*

4. **Guard Verification Terminal (Gate 1):**  
   `docs/screenshots/04_guard_verification.png`  
   *Displays camera viewport, student face verification card, and Confirm Exit/Entry actions.*

5. **Analytics & Curfew Compliance Dashboard:**  
   `docs/screenshots/05_analytics_dashboard.png`  
   *Displays gate-wise traffic volume, late-return percentages, and CSV dataset analytics.*

---

## 19. Sample Output from Working CSV Analysis

Running `python analyze_data.py data.csv` produces the following real administrative report:

```text
=================================================================
GATEPASS - HOSTEL OUTPASS MANAGEMENT SYSTEM
DEMONSTRATION ANALYTICS REPORT (from data.csv)
=================================================================
DATASET PROVENANCE: SYNTHETIC DEMO DATASET - Fictional development records for take-home assignment testing.
-----------------------------------------------------------------
Total Outpass Records Analyzed : 52
  - Completed Journeys         : 24
  - Currently Outside Campus   : 6
  - Approved (Ready to Exit)   : 8
  - Rejected Requests          : 6
  - Pending Warden Review      : 8
-----------------------------------------------------------------
Late Returns Identified        : 4 (7.7%)
Average Outpass Duration       : 2h 57m (177.0 mins)
-----------------------------------------------------------------
Gate-wise Movement Traffic:
  Gate 1    : Exits = 10  | Entries = 9   | Total = 19
  Gate 2    : Exits = 6   | Entries = 5   | Total = 11
  Gate 3    : Exits = 7   | Entries = 5   | Total = 12
  Gate 4    : Exits = 7   | Entries = 5   | Total = 12
-----------------------------------------------------------------
Student Program Breakdown:
  M.Tech    : 12 requests
  B.Tech    : 30 requests
  PhD       : 10 requests
=================================================================
```

---

## 20. Security Considerations

1. **Password Hashing:** Passwords are never stored in plaintext; hashed using Werkzeug's implementation of secure password hashing (`generate_password_hash`).
2. **Session Security & RBAC:** Role-based access control enforces that students cannot approve passes or access warden consoles, and guards can only confirm gate movements.
3. **No Sensitive Data in QR Codes:** The QR code encodes *only* a high-entropy random hex token (`secrets.token_hex(16)`). It does not embed student names, passwords, roll numbers, or contact numbers.
4. **Server-Side State Machine Enforcement:** A QR scan does not blindly record movements. The authenticated guard must verify the student and confirm the action. The server strictly rejects duplicate exits or entries.
5. **CSRF Protection:** State-modifying POST requests require session-bound cryptographic CSRF tokens.
6. **SQL Injection Prevention:** All database operations utilize parameterized queries (`?` placeholders) with strict SQLite typing.

---

## 21. Current Limitations
- **Prototype Scope:** Built as an MVP for a 24-hour evaluation sprint; does not include physical hardware turnstile relays.
- **Camera Permissions:** HTML5 camera scanning requires `localhost` or HTTPS when accessed over a local Wi-Fi network. The manual passcode fallback provides full operational parity.
- **Single-Tenant Database:** Utilizes SQLite WAL mode suitable for demo scale; a production campus deployment across 5,000+ students would migrate to PostgreSQL.

---

## 22. Future Improvements
- **SMS / WhatsApp Gateway Integration:** Automated Twilio / MSG91 alert dispatch to parents or wardens when a student is overdue past 10:00 PM.
- **Turnstile IoT Relay Controller:** Raspberry Pi or ESP32 GPIO integration to automatically trigger physical turnstile locks on guard confirmation.
- **Offline PWA Support:** Service Worker caching to permit gate logging even during temporary Wi-Fi drops.

---

## 23. Demonstration Video Link
- **Screen Recording (3 Minutes):** `[Link to screen recording / YouTube / Google Drive]` *(Awaiting recording)*
- *Walkthrough checklist for video:* Student application &rarr; Warden approval &rarr; QR pass generation &rarr; Guard exit confirmation &rarr; Guard entry confirmation &rarr; Late alert demonstration.

---

## 24. Synthetic Data Disclosure
All student names, roll numbers, room assignments, warden credentials, and movement logs included in `seed.py` and `data.csv` are **fictional synthetic demonstration records**. They were generated algorithmically to test edge cases (duplicate scans, multi-gate transits, late curfew returns) without exposing real student privacy.

---

## 25. Assignment Requirement Checklist

| Requirement | Category | Status | Notes |
|---|---|---|---|
| Problem description in 5 lines | Research | **Completed** | Documented in `research.md` |
| 2 existing solutions analyzed | Research | **Completed** | Turnstiles & Visitor SaaS evaluated in `research.md` |
| 2 sources read with 3-line notes | Research | **Completed** | Published literature cited in `research.md` |
| Working Flask application | Build | **Completed** | Full monolith running in `app.py` |
| Role-based dashboards (Student/Warden/Guard) | Build | **Completed** | All 3 responsive portals implemented |
| 4 Campus Gates supported | Build | **Completed** | Gate 1, Gate 2, Gate 3, Gate 4 |
| Multi-gate transit (Exit Gate 1 &rarr; Enter Gate 3) | Build | **Completed** | Implemented and verified in `models.py` |
| Cryptographic QR generation & scan | Build | **Completed** | In-memory base64 QR + HTML5 camera scanner |
| Manual passcode fallback | Build | **Completed** | Tested and functional on `/guard/verify` |
| Automated curfew (10 PM) & late return flags | Build | **Completed** | IST timezone evaluator in `models.py` |
| In-app notification center | Build | **Completed** | Database-backed alerts + unread counter |
| CSV reader & analytical report | Build | **Completed** | `analyze_data.py` + Web Analytics view |
| Automated test suite (14+ test cases) | Build | **Completed** | 16 tests passing in `tests/` |
| Synthetic demo data (50+ female students) | Build | **Completed** | 52 female students, 52 outpass records via `seed.py` |
| 20-minute physical visit | Fieldwork | **Completed** | Documented in `fieldwork.md` |
| 2 timestamped photographs | Fieldwork | **Completed** | Gate Register Page 1 & 2 in `static/images/` |
| Conversation with real person & 3 quotes | Fieldwork | **Completed** | Guard R. K. Mishra interview in `fieldwork.md` |
| 1 surprising observation | Fieldwork | **Completed** | Informal WhatsApp coordination in `fieldwork.md` |
| 20 self-collected real data entries | Fieldwork | **Completed** | 20 real observation rows in `fieldwork.md` |
| Half-page personal reflection | Reflection | **Drafted** | Personal engineering reflection in `reflection.md` |
| Screen recording (3 mins) | Submission | **Action Required** | Record 3-min walkthrough & paste link in Section 23 |

---

## Git Commit Schedule & Instructions

For the assignment requirement of genuine, distributed Git commits throughout your development day:

```bash
# 1. Initialize Git repository
git init

# 2. Commit 1 (Hour 1 - Research & Problem Definition)
git add research.md requirements.txt .gitignore
git commit -m "feat(research): initial problem statement, existing solutions review, and literature notes"

# 3. Commit 2 (Hour 3 - Core Architecture & Database Models)
git add config.py database.py models.py
git commit -m "feat(backend): implement SQLite schema, IST timezone engine, and outpass models"

# 4. Commit 3 (Hour 6 - Student & Warden Modules)
git add app.py templates/student/ templates/warden/ static/
git commit -m "feat(portals): implement student outpass application and warden approvals inbox"

# 5. Commit 4 (Hour 9 - Guard Terminal & QR Verification)
git add templates/guard/ static/js/main.js
git commit -m "feat(security): implement multi-gate guard verification and HTML5 QR camera scanner"

# 6. Commit 5 (Hour 12 - Data Intelligence & Automated Tests)
git add seed.py analyze_data.py data.csv tests/
git commit -m "test(suite): add 16 automated end-to-end integration tests and CSV analytics"

# 7. Commit 6 (Hour 15 - Documentation & Submission Deliverables)
git add README.md fieldwork.md reflection.md ai-chats/
git commit -m "docs: finalize comprehensive technical README, fieldwork logs, reflection and AI portfolio"
```
