# AI Chat Log 02: Outpass Verification, Lateness Rules & Multi-Gate State Transitions

**User:**
Let's implement the backend logic in `models.py`. I need strict business rules:
1. When a student applies, an outpass is in `PENDING` status. No QR code or verification token should be active yet.
2. When the Warden approves, a secure token should be generated and outpass becomes `APPROVED`. If the warden rejects, they must provide a reason.
3. At the gate: The guard at Gate 1 scans or looks up the pass. If the pass is `APPROVED`, they see a big "Confirm EXIT" button. Once clicked, it changes status to `OUTSIDE`. If they click it again, it must strictly prevent duplicate exit!
4. What if the student returns through Gate 3 instead of Gate 1? How do we handle multi-gate returns?
5. When is a student considered late? Campus curfew is 10 PM, but what if their approved expected return was 8 PM and they returned at 9 PM?

---

**Assistant:**
Here is how we will enforce those exact business rules:

### 1. Multi-Gate State Enforcement
We enforce server-side validation on state transitions:
```python
def record_gate_exit(outpass_id, guard_id, gate_name):
    # Check if already OUTSIDE or COMPLETED
    if pass_data["status"] == "OUTSIDE":
        return False, "Duplicate Exit Prevented: Student is already marked OUTSIDE."
    if pass_data["status"] != "APPROVED":
        return False, f"Cannot exit: Pass is in {pass_data['status']} status."
    # Update status to OUTSIDE, insert row in gate_logs with movement_type='EXIT'
```

For Entry at Gate 3:
```python
def record_gate_entry(outpass_id, guard_id, gate_name):
    # Can only enter if currently OUTSIDE
    if pass_data["status"] != "OUTSIDE":
        return False, f"Cannot record entry: Student is not OUTSIDE."
    # Update status to COMPLETED, insert row in gate_logs with movement_type='ENTRY'
    # Gate name is saved as Gate 3, even if exit was Gate 1!
```

### 2. Dual-Layer Lateness Evaluation
A student is late if:
- `actual_return > min(expected_return_datetime, 22:00)`
- If a student promised 8:00 PM and returns at 9:00 PM, they are 60 minutes late past approved return.
- If a student promised 9:45 PM and returns at 10:25 PM, they are 25 minutes late past campus curfew.
Both minutes and reason are stored and flagged on the warden dashboard in real-time.
