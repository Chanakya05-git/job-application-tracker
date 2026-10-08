# Job Application Tracker

A small, local command-line tracker for recording job applications, updating their status, reviewing a pipeline summary, and preparing follow-up email drafts. Application records are stored as JSON in `data/applications.json`.

## Features

- Log company, role, application date, and notes.
- Track applications as `applied`, `interviewing`, `offer`, `rejected`, or `withdrawn`.
- Display counts for every status, including statuses with no applications.
- Calculate a suggested follow-up date, seven days after applying by default.
- Review the exact proposed JSON diff before any local save.
- Optionally draft a follow-up email with Gemini. The app drafts text only; it does not send email.

## Requirements

- Python 3.10 or newer.
- No third-party packages are needed for the core tracker.
- Gemini email drafting optionally uses Google's `google-genai` package and a Gemini API key.

## Installation and Start

From the project directory, check that Python is available:

```sh
python3 --version
```

Start the interactive CLI:

```sh
python3 main.py
```

On first run, the tracker loads an empty pipeline if `data/applications.json` does not exist. The file is created when you approve the first save.

## Using the CLI

The menu provides these actions:

1. Log an application.
2. Update an application's status.
3. Display the pipeline summary.
4. Draft a follow-up email with Gemini.
5. Exit.

For example, choose `1` and enter the requested company, role, date, and notes. The application is added to the in-memory pipeline, then the tracker displays the unified diff between the saved JSON and the proposed version. Review the diff before responding:

```text
Save these changes? Type yes, confirm, or save (or no to cancel): maybe
Response rejected. Enter yes, confirm, or save; use no or cancel to abort.
Save these changes? Type yes, confirm, or save (or no to cancel): confirm
```

Approval words are case-insensitive. `no`, `n`, or `cancel` aborts the save. Any other response is rejected and the program asks again. If you cancel, the proposed in-memory log or status change is rolled back. When the save is approved, the complete pipeline is written to `data/applications.json`.

To update a status, choose the application by its displayed number and enter one of the supported status values. To view the summary, choose option `3`.

## Stored Data

Each JSON record contains these fields:

```json
{
  "company": "Acme Corp",
  "role": "Software Engineer",
  "date_applied": "2026-10-08",
  "status": "applied",
  "notes": "Follow up next week"
}
```

The data file is local and plain text. Back it up like any other important file. The approval diff includes additions, edits, and removals between the saved data and the proposed full pipeline.

## Optional Gemini Email Drafts

Install the optional SDK:

```sh
python3 -m pip install google-genai
```

Set `GEMINI_API_KEY` in your shell before starting the tracker. For zsh, replace the placeholder with your key:

```sh
export GEMINI_API_KEY="YOUR_API_KEY"
python3 main.py
```

Choose option `4`, select an application, and confirm before the application details are sent to Gemini. The current request includes the company, role, application date, and status; notes are not sent. The default model is `gemini-2.5-flash`. The returned draft is printed in the terminal and is not stored or sent to anyone.

## Running Tests

The test suite uses Python's built-in `unittest` framework and temporary files, so it does not read or modify your real application data:

```sh
python3 -m unittest discover -s tests -v
```

Tests cover normal tracker behavior, empty company names, invalid statuses, past and malformed deadlines, JSON round trips, approval diff output, accepted approval words, vague-input retries, and cancellation without writes.

## Known Limitations

- Records live in one local JSON file. There is no database, encryption, cloud synchronization, multi-user support, or file locking.
- Follow-up dates are suggestions only. The tracker does not create calendar events, send reminders, or schedule notifications.
- The CLI does not currently collect or persist a search goal or deadline. `session_state` has fields for these values, but they are not wired into the current workflow or JSON format.
- Gemini is optional and requires network access, an API key, and a separately installed SDK. Application details are sent to Google's Gemini service only after confirmation; consider your privacy and applicable data policies.
- Gemini drafts may need review and editing. The app does not verify facts in a draft or send it.
- There is no dedicated delete action in the CLI. If the proposed full pipeline removes records, the JSON diff shows those removals and the same explicit approval gate applies.
