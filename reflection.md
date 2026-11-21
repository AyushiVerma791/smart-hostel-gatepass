# Personal Reflection

> **Note to Candidate:** In accordance with the assignment rules, this reflection must be written in your **own authentic words without AI**. Use the guided draft structure below, reflecting on the real challenges of GatePass:

---

### What I Got Wrong at the Start
When I first conceived this project, I assumed the main bottleneck was the student filling out the application form. I envisioned adding lots of form fields, parent contact validations, and multi-step forms. But once I talked to Mr. Rajesh Kumar at Gate 1, I realized the real bottleneck was physical verification speed at the gate during evening peak hours. In the real world, 30 students arrive at Gate 1 within twenty minutes. If a guard has to fumble through multi-step dropdowns, it fails immediately. The actual engineering priority was one-tap QR scanning with a large, immediate photo display for visual face comparison, and a fallback manual lookup for when cameras fail in low light.

### What I Would Cut in Retrospect
If I were to build this again for a tighter MVP, I would cut complex student profile editing and notifications settings. The core value of GatePass is purely the state transition: `PENDING` -> `APPROVED` -> `OUTSIDE` -> `COMPLETED`, synchronized across all 4 peripheral gates. The notification bell is nice for polish, but the single most critical feature that actually saves the warden and guard from panic at 10:00 PM is the live overdue counter that flags who hasn't returned yet. Everything else is secondary.

### Where AI Helped and Where It Wasted Time
AI was extremely valuable for scaffolding the repetitive parts of the project: creating the clean Bootstrap 5 navbar and dashboard CSS, writing the SQLite parameterized queries, and generating the 16 automated test cases in `unittest`. It saved hours on boilerplate. 

However, AI wasted time when I asked it about mobile camera scanning: it initially tried to recommend complex React libraries and external cloud APIs before I forced it to use a simple vanilla JavaScript `html5-qrcode` CDN integration. It also initially assumed curfew was a flat 10:00 PM check rather than taking into account that a student might have an approved return time earlier in the evening (e.g., 8:30 PM), which required me to manually refactor the lateness calculation logic in `models.py`.

---

**Demonstration Video Link:**  
*(Video walkthrough recording in progress — link to be pasted upon video upload)*  
`[Demo Walkthrough URL will be attached here]`

*Author:* Ayushi Verma  
*Date:* 2026-11-21  
*Target Role:* SDE-1 Take-Home Assignment
