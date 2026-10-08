# Job Application Tracking AI Assistant

A local, single-user CLI tool for logging job applications, tracking their
statuses, and generating follow-up reminders — with a strict human approval
gate before any local data is written.

## Features

- **Log applications** — company, role, date applied, status, and notes.
- **Track statuses** — `applied`, `interviewing`, `offer`, `rejected`,
  `withdrawn`.
- **Pipeline summaries** — grouped by status with counts.
- **Follow-up dates** — computed per application from its status window
  (applied: +7 days, interviewing: +3 days, offer: +7 days,
  rejected/withdrawn: none).
- **Follow-up email drafts** (optional) — generated with the Gemini API.
- **Persistent storage** — `data/applications.json`, loaded on startup.
- **Approval gate** — before any write, the exact JSON diff is shown and only
  explicit confirmation (`yes` / `confirm` / `save`) saves; vague inputs like
  `"maybe"` are rejected and re-prompted.

## Installation

Requires Python 3.9+.

```bash
cd "Default Project"
# Optional, only needed for the email-draft feature:
pip install google-generativeai
export GEMINI_API_KEY="your-api-key"
```

## Usage

Run the interactive CLI:

```bash
python3 main.py
```

```text
Job Application Tracker
  1. Log a new application
  2. Update application status
  3. Show pipeline summary
  4. Show follow-up dates
  5. Draft follow-up email (Gemini)
  6. Exit
```

Example session (logging an application):

```text
Choose an option: 1
Company: Acme Corp
Role: Software Engineer
Date applied (YYYY-MM-DD, blank = today): 2026-10-01
Status (applied/interviewing/offer/rejected/withdrawn) [applied]: applied
Notes: Referred by Jane

Proposed changes:
--- data/applications.json (current)
+++ data/applications.json (proposed)
@@ ...
Save changes? Type "yes", "confirm", or "save" to approve: yes
Logged and saved application to Acme Corp.
```

A rejected confirmation leaves `data/applications.json` untouched (and the
change is rolled back from the in-memory pipeline):

```text
Save changes? ...: maybe
Rejected: "maybe" is not an explicit confirmation. ...
Save changes? ...: no
Cancelled — data/applications.json left unchanged.
```

### Library usage

```python
import tracker, storage

app = tracker.log_application("Acme Corp", "Engineer", "2026-10-01")
print(tracker.format_pipeline_summary())
print(tracker.calculate_follow_up_date(app))
# storage.save_applications([a.to_dict() for a in tracker.session_state["pipeline"]])
```

## Running the tests

```bash
python3 -m unittest discover -s tests
```

Covers normal inputs, edge cases (empty company names, invalid statuses, past
deadlines), and approval-gate rejection/re-prompting.

## Project structure

```text
main.py        # interactive CLI entry point
tracker.py     # session_state, Application model, tracking helpers, Gemini draft
storage.py     # JSON persistence + diff approval gate
validation.py  # company/status/deadline validators
data/          # applications.json lives here
tests/         # unittest suite
```

## Known limitations

- **Local, single-user**: no concurrent-access handling for
  `data/applications.json`.
- **Date handling is strict**: `date_applied` must be `YYYY-MM-DD`; deadline
  validation is separate and rejects past dates (a past `date_applied` is
  allowed, as it should be).
- **Follow-up windows are hardcoded** per status in `FOLLOW_UP_WINDOWS`.
- **Gemini drafting is optional**: requires the `google-generativeai` package
  and `GEMINI_API_KEY`; without them the helper raises a clear error and the
  rest of the app is unaffected.
- **No deletion UI**: record removal is not exposed in the CLI yet (the
  approval-gate machinery is ready to reuse for it).
- **No resume/career-profile integration**: statuses are tracked manually.
