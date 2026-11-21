# AI Chat Log 01: System Architecture, Real Problem & Database Design

**User:**
I am building a 24-hour take-home assignment project for an SDE-1 role. The problem is right on my campus: female hostel residents have to get paper outpasses from the warden to leave campus after 6 PM. The paper slips get lost, guards at 4 different gates manually write entries in registers, and if a girl leaves through Gate 1 and returns through Gate 3, nobody knows she is back. The warden has no real-time idea who is outside past the 10 PM curfew. 

I want to build a lightweight web application in Python, Flask, SQLite, Bootstrap 5. Help me design the normalized relational schema and state machine. It must support 3 roles: Student, Warden, and 4 Guard accounts (Gate 1 to Gate 4). What should the tables look like?

---

**Assistant:**
That is a practical campus problem with a clear state lifecycle. Here is the architectural plan:

### 1. State Machine Lifecycle
We must define clean, non-reversible states to prevent duplicate exits or entries:
`PENDING` -> `APPROVED` -> `OUTSIDE` -> `COMPLETED` (or `REJECTED`)

### 2. Normalized SQLite Schema:
- **`users` Table:**
  - `id`, `name`, `roll_number` (unique), `email`, `role` (student/warden/guard), `program` (B.Tech/M.Tech/PhD), `department`, `hostel`, `room`, `avatar`, `password_hash`, `gate_name`.
- **`outpasses` Table:**
  - `id`, `pass_code` (e.g., GP-2026-0001), `student_id`, `destination`, `purpose`, `departure_date`, `departure_time`, `planned_exit_datetime`, `expected_return_datetime`, `declaration_agreed`, `status`, `warden_id`, `approved_at`, `rejection_reason`, `verification_token`.
- **`gate_logs` Table:**
  - `id`, `outpass_id`, `student_id`, `guard_id`, `gate_name`, `movement_type` (`EXIT` or `ENTRY`), `timestamp`, `notes`.
- **`notifications` Table:**
  - `id`, `user_id`, `title`, `message`, `category`, `is_read`, `created_at`.

### 3. Key Design Decisions:
1. Multi-gate capability: Exit gate and Entry gate are logged as separate rows in `gate_logs` linked to the same outpass. So Gate 1 exit + Gate 3 entry works seamlessly.
2. Privacy: The QR code encodes only a 32-character high-entropy cryptographic token, never raw student passwords or phone numbers.
3. Guard visual verification: When scanned, the guard terminal fetches the student's photo from the server so the guard physically compares the student's face before pressing Confirm Exit.
