# Final Project Execution Plan

## Goal
Build a working webcam-based smart attendance system that identifies registered students,
records attendance automatically, calculates attendance percentage, flags low attendance,
supports condonation review, and generates reports.

## Frozen architecture
Webcam -> OpenCV -> Face Detection -> Face Encoding/Recognition -> Student Matching ->
Attendance Validation -> SQLite Database -> Dashboard -> Reports/Alerts

## Week 1 — Foundation
Install Python, VS Code/PyCharm, Git and packages. Verify webcam/OpenCV.
Finalize requirements. Build initial Tkinter screens. Create SQLite database/schema.
Collect consented face samples.
**Output:** webcam works, database works, face samples are stored.

## Week 2 — Recognition
Build student registration, face capture, face detection, face encoding and recognition.
Test known and unknown faces separately.
**Output:** reliable recognition prototype.

## Week 3 — Attendance
Connect recognition to attendance. Add subject/session/date/time, duplicate prevention,
percentage calculation, status indicators, low-attendance alerts and condonation review.
**Output:** complete core attendance workflow.

## Week 4 — Reports and evaluation
Build dashboard and daily/monthly/subject/student reports. Add Excel/PDF export.
Run formal accuracy tests, false-acceptance/rejection tests and response-time tests.
Fix bugs and prepare screenshots, graphs, research paper, final report and presentation.
**Output:** tested final prototype and documentation.

## Accuracy protocol
Use separate enrollment and test data. Record correct recognitions, wrong recognitions,
missed recognitions, unknown-person acceptance/rejection and response time.

Recognition accuracy = correctly recognized test cases / total test cases * 100.

Never fabricate accuracy or claim 100% without measured evidence.

## Acceptance tests
- Registration saves correct details and face samples.
- Known student is recognized.
- Unknown person is not assigned to a registered student.
- Duplicate attendance is blocked.
- Multiple students can be processed.
- Percentage matches database records.
- Status indicators are correct.
- Low attendance is flagged.
- Reports match database totals.
- Unauthorized users cannot edit protected records.
- Camera failure/no-face conditions do not crash the application.

## Scope control
Do not add mobile app, cloud deployment, multiple cameras, large custom model training,
emotion recognition, GPS tracking or complete ERP until the core system is stable.

## Final deliverables
Working Python application, OpenCV recognition module, SQLite database, registration,
attendance dashboard, percentage/alerts, condonation review, reports, Excel/PDF export,
accuracy tables/graphs, Git backup, final report, research paper and presentation.
