# AI Chat Log 03: Guard Station UI, Camera Scanning & Fallbacks

**User:**
The guards are non-technical and use different budget Android phones. How should we build the QR scanning and visual verification? Can we use `html5-qrcode`? What happens if camera permissions are blocked on plain HTTP on the local network?

---

**Assistant:**
Great consideration for real campus hardware conditions:

1. **Lightweight HTML5 QR Scanner:**
   We integrate `html5-qrcode` via CDN (`https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js`). When the guard clicks "Start Camera", it requests the device rear environment camera and decodes the QR token.

2. **Crucial Fallback: Manual Pass Code Entry:**
   Mobile browsers block camera streams on non-secure HTTP origins (unless on `localhost`). To guarantee the guard is never locked out:
   - Every digital pass displays a human-readable pass ID like `GP-2026-0007`.
   - The guard terminal includes a prominent manual input field where the guard can type or paste the code and press Enter.
   - The backend looks up both the cryptographic token and the pass code with equal reliability.

3. **High-Contrast Identity Verification UI:**
   When verified, the screen displays:
   - High-contrast alert header (Green for valid exit, Blue for valid return, Red for invalid/expired).
   - Large student profile photograph with a yellow "VERIFY FACE" badge.
   - Name, Roll Number, Room Number, Approved Destination, and Expected Return Time.
   - Huge action button (`CONFIRM EXIT` or `CONFIRM ENTRY`) that logs the exact gate and timestamp to the central database.
