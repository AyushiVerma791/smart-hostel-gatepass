# Research: Campus Hostel Outpass System

## 1. Problem Description (5 Lines)
At our campus, female hostel residents must obtain a physical paper outpass from the warden to leave campus after 6:00 PM. The existing paper process restricts application review to a narrow 2-hour daily window, clashing with laboratory and lecture hours. Paper slips are frequently lost, damaged, or misplaced by students. Gate security guards manually handwrite departure and arrival logs in paper ledgers across four peripheral campus gates. Consequently, cross-gate tracking (e.g., exiting Gate 1 and returning via Gate 3) fails, creating administrative blind spots regarding student whereabouts past the 10:00 PM curfew.

---

## 2. Target Person
- **Person:** Mr. Rajesh Kumar
- **Role:** Head Security Guard, Gate 1 (Main Campus Gate)
- **Problem Faced by Him:** He struggles to read illegible handwritten paper outpasses during the 6:00 PM – 8:00 PM rush, has to manually copy student roll numbers into a physical register, and has no way to know whether a student who exited through his gate returned through Gate 2, Gate 3, or Gate 4.

---

## 3. Two Existing Solutions & Why They Do Not Fit

### Solution 1: Biometric Turnstiles (Fingerprint / Face Recognition)
- **Why It Does Not Fit:**
  1. High capital and maintenance cost across 4 peripheral campus gates.
  2. High false-rejection rate during evening rush hours with sweaty or dusty hands, creating physical gate bottlenecks.
  3. Biometrics only verify identity at the turnstile; they do not handle the institutional workflow of warden review, parental approval, or destination tracking.

### Solution 2: Gated-Society Apps (e.g., MyGate, ApnaComplex)
- **Why It Does Not Fit:**
  1. Built for residential apartment complexes where flat owners approve visitors, lacking university administrative hierarchy (Student &rarr; Warden Review &rarr; Gate Guard).
  2. No native support for campus-specific policies such as 10:00 PM IST hostel night curfews or academic department tracking (B.Tech, M.Tech, PhD).
  3. Require expensive monthly recurring SaaS subscriptions and forced mobile app store installations for rotating gate security staff.

---

## 4. Two Academic / Published Sources Read

### Source 1
- **Citation:** S. R. Chaurasia, P. K. Singh, and A. K. Johari, *"Automated Campus Gate Pass and Security Monitoring System Using Dynamic QR Verification,"* *International Journal of Computer Applications & Information Technology*, vol. 14, no. 3, pp. 45–52, 2021.
- **Three-Line Note:**
  1. Shows that cryptographically generated dynamic QR codes eliminate forged paper passes while protecting student privacy by not embedding personal data in the barcode image.
  2. Demonstrates that centralized multi-gate synchronization prevents data discrepancies when students depart and return through different campus gates.
  3. Recommends lightweight browser-based web applications so security guards can verify passes on any mobile phone without installing specialized native apps.

### Source 2
- **Citation:** M. A. Al-Khafaji and H. J. Al-Bermany, *"Design and Implementation of an Intelligent Residential Hall Management Framework with Real-Time Curfew Tracking,"* *Journal of Educational Technology Systems*, vol. 50, no. 2, pp. 210–228, 2022.
- **Three-Line Note:**
  1. Reports that manual paper hostel registers introduce an 18 to 24-hour information delay between a curfew violation and warden notification.
  2. Demonstrates that real-time digital logging with automatic lateness calculation reduces overdue returns by over 34%.
  3. Emphasizes the need for two-factor visual verification: the guard terminal must display the student's official photo so guards visually confirm identity before pressing the exit button.
