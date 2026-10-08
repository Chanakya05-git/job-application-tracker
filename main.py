"""Entry point for the tracker application."""

from datetime import datetime

import storage
import tracker
from validation import validate_status

MENU = """
Job Application Tracker
  1. Log a new application
  2. Update application status
  3. Show pipeline summary
  4. Show follow-up dates
  5. Draft follow-up email (Gemini)
  6. Exit
"""


def _load_pipeline() -> None:
    for record in storage.load_applications():
        tracker.session_state["pipeline"].append(tracker.Application(**record))


def _save_pipeline() -> bool:
    return storage.save_applications(
        [app.to_dict() for app in tracker.session_state["pipeline"]]
    )


def _confirm(prompt: str) -> bool:
    return input(f"{prompt} [y/N]: ").strip().lower() in ("y", "yes")


def _log_application_cli() -> None:
    from validation import validate_company_name

    company = input("Company: ").strip()
    role = input("Role: ").strip()
    date_applied = input("Date applied (YYYY-MM-DD, blank = today): ").strip()
    if not date_applied:
        date_applied = datetime.today().strftime("%Y-%m-%d")
    status = input(
        f"Status ({'/'.join(tracker.VALID_STATUSES)}) [applied]: "
    ).strip() or "applied"
    notes = input("Notes: ").strip()

    try:
        validate_company_name(company)
        validate_status(status)
        datetime.strptime(date_applied, "%Y-%m-%d")
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    app = tracker.log_application(company, role, date_applied, status, notes)
    if _save_pipeline():
        print(f"Logged and saved application to {app.company}.")
    else:
        tracker.session_state["pipeline"].remove(app)
        print("Application discarded — nothing saved.")


def _update_status_cli() -> None:
    company = input("Company: ").strip()
    role = input("Role (blank = match any): ").strip() or None

    match = next(
        (
            a
            for a in tracker.session_state["pipeline"]
            if a.company.lower() == company.lower()
            and (role is None or a.role.lower() == role.lower())
        ),
        None,
    )
    if match is None:
        print("No matching application found.")
        return

    new_status = input(
        f"New status ({'/'.join(tracker.VALID_STATUSES)}): "
    ).strip()
    try:
        validate_status(new_status)
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    print(f"\n{match.company} | {match.role}: {match.status} -> {new_status}")
    old_status = match.status
    tracker.update_status(company, new_status, role=role)
    if _save_pipeline():
        print("Status updated and saved.")
    else:
        match.status = old_status
        print("Status update discarded — no changes saved.")


def _summary_cli() -> None:
    print(tracker.format_pipeline_summary())


def _follow_ups_cli() -> None:
    pipeline = tracker.session_state["pipeline"]
    if not pipeline:
        print("Pipeline is empty.")
        return
    print("\nFollow-up dates:")
    for app in pipeline:
        follow_up = tracker.calculate_follow_up_date(app)
        if follow_up is None:
            print(f"  {app.company} — {app.role}: no follow-up ({app.status})")
        else:
            print(f"  {app.company} — {app.role}: follow up on {follow_up.isoformat()}")


def _draft_email_cli() -> None:
    company = input("Company: ").strip()
    match = next(
        (
            a
            for a in tracker.session_state["pipeline"]
            if a.company.lower() == company.lower()
        ),
        None,
    )
    if match is None:
        print("No application found for that company.")
        return

    if not _confirm("Call the Gemini API to draft a follow-up email?"):
        print("Cancelled — no API call made.")
        return

    try:
        email = tracker.draft_follow_up_email(match)
    except RuntimeError as exc:
        print(f"Cannot draft email: {exc}")
        return

    print("\n--- Draft follow-up email ---")
    print(email)
    print("-----------------------------")


def main() -> None:
    _load_pipeline()
    actions = {
        "1": _log_application_cli,
        "2": _update_status_cli,
        "3": _summary_cli,
        "4": _follow_ups_cli,
        "5": _draft_email_cli,
    }

    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()
        if choice == "6":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action is None:
            print("Invalid option — please choose 1-6.")
            continue
        action()


if __name__ == "__main__":
    main()
