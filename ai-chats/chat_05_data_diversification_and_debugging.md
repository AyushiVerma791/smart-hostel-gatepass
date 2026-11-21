# AI Exchange Log 05: Data Diversification, Real Field Evidence & Bug Diagnosis

## Context
During local testing of the GatePass monolith, the candidate identified two critical areas for refinement before final delivery:
1. **Realistic Student Roster Diversification:** Expanding roll numbers beyond single-cohort demo prefixes to represent 4-year undergraduate degree cycles (`IIT2022xxx` through `IIT2025xxx`, `IEC2022xxx` through `IEC2025xxx`), specialized postgraduate M.Tech branches (`MRH` for Robotics & Hardware, `MNS` for Networks & Security, `MCL` for Cloud Systems, `MSD` for Software Development, `MBI` for Bioinformatics, `MWC` for Wireless Communication), and doctoral scholars (`PHD2021xxx` through `PHD2025xxx`).
2. **Fieldwork Grounding:** Ingesting photographic evidence of the physical paper ledger (signed by Head Guard R. K. Mishra at Gate 1) into `static/images/` and aligning `fieldwork.md`.
3. **Approvals Inbox Bug Diagnosis:** Resolving an issue where the Warden Dashboard KPI showed 9 pending outpass requests, but navigating to `/warden/approvals` rendered 0 records.

---

## Prompt Excerpt 1 (Candidate):
> *"for mtech , dont just use mwc in roll no , also use mrh, mns, mcl, msd, etc because the branched are different and also as btech are from 4 year, you can give roll no also iit2023005, iit2024009 etc kind of roll nos"*

### AI Assistance:
- Refactored `STUDENT_DATA` in `seed.py` into distinct academic cohorts:
  - B.Tech 4th Year (Batch 2022): `IIT2022001`, `IEC2022004`, `IIT2022015`, `IEC2022018`, etc.
  - B.Tech 3rd Year (Batch 2023): `IIT2023005`, `IEC2023008`, `IIT2023014`, `IEC2023019`, etc.
  - B.Tech 2nd Year (Batch 2024): `IIT2024009`, `IEC2024003`, `IIT2024016`, `IEC2024021`, etc.
  - B.Tech 1st Year (Batch 2025): `IIT2025002`, `IEC2025006`, `IIT2025011`, `IEC2025017`, etc.
  - M.Tech (Batches 2024–2025): `MRH`, `MNS`, `MCL`, `MSD`, `MWC`, and `MBI`.
  - PhD Scholars (Batches 2021–2025): `PHD2021001` through `PHD2025005`.
- Automated generation of 52 matching SVG initials avatars in `static/avatars/`.
- Re-generated synthetic dataset in `data.csv`.

---

## Prompt Excerpt 2 (Candidate):
> *"i am not getting that when i make one outpass, and after words i login with warden there was written that 9 requirest are pending, but when we went to the pending option, there inside they show 0 pending, what is this?, correct the mistake so that i could record"*

### Root Cause Analysis:
- Evaluated `get_all_movements()` in `models.py`.
- Discovered an existing query clause with hardcoded filtering:
  ```sql
  WHERE o.status IN ('APPROVED', 'OUTSIDE', 'COMPLETED')
  ```
- When `warden_approvals` requested `status_filter='PENDING'`, the resulting SQL condition became:
  ```sql
  WHERE o.status IN ('APPROVED', 'OUTSIDE', 'COMPLETED') AND o.status = 'PENDING'
  ```
- Because a row cannot simultaneously belong to both sets, SQLite returned 0 records.

### Resolution:
- Updated the filter logic to dynamically branch:
  ```python
  if status_filter:
      query += " AND o.status = ?"
      params.append(status_filter)
  else:
      query += " AND o.status IN ('APPROVED', 'OUTSIDE', 'COMPLETED')"
  ```
- Re-ran `get_all_movements(status_filter='PENDING')`: successfully returned all 9 pending records.
- Executed full test suite: 16/16 integration tests passing in `tests/`.
- Pushed fix commit to remote repository.
