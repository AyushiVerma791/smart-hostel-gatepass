# AI Chat Log 04: Automated Tests, CSV Analysis & Edge Cases

**User:**
The take-home assignment requires automated tests for the whole workflow and a CSV reading script `analyze_data.py`. 
Please write comprehensive unit tests in Python covering:
1. Student login and role access checks.
2. Outpass submission and warden approval.
3. Guard exit confirmation and duplicate exit blocking.
4. Multi-gate entry and duplicate return blocking.
5. Curfew lateness calculations.
6. Handling missing or malformed CSV rows.

Also, write `analyze_data.py` to calculate gate loads, average duration, and delinquency rates.

---

**Assistant:**
Here is the implementation strategy:

### 1. Test Suite (`tests/` using `unittest`):
- `test_auth.py`: Tests password hash verification, role session injection, unauthenticated redirects, and unauthorized role blocks (e.g. student trying to hit `/warden/dashboard`).
- `test_outpass.py`: Tests outpass creation in `PENDING` state, warden approval triggering token generation, and ensures rejected requests cannot be used at gates.
- `test_gate.py`: Tests exit logging, duplicate exit prevention, multi-gate transition (exit Gate 1, return Gate 3), duplicate return prevention, and 3 lateness scenarios (on-time, past expected return, and past 10 PM curfew).
- `test_analytics.py`: Tests CSV parser resilience against missing files and malformed CSV headers.

### 2. Analytical Engine (`analyze_data.py`):
Reads `data.csv`, computes:
- Total outpass volume and status counts
- Average recorded duration in hours and minutes
- Gate traffic breakdown (Exits vs Entries per gate: Gate 1, 2, 3, 4)
- Program demographics (B.Tech, M.Tech, PhD)
- Lateness delinquency percentage
Includes CLI formatted report generator (`python analyze_data.py`).
