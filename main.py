from datetime import date

from storage import load_applications, save_applications
from tracker import (
    Application,
    calculate_follow_up_date,
    draft_follow_up_email,
    log_application,
    session_state,
    summarise_pipeline,
    update_status,
)
from validation import APPLICATION_STATUSES, validate_company_name, validate_status


def _confirm(prompt: str) -> bool:
    return input(f"{prompt} Type 'yes' to confirm: ").strip().lower() == "yes"


def _save_pipeline() -> bool:
    return save_applications(session_state["current_pipeline"])


def _show_applications() -> None:
    applications = session_state["current_pipeline"]
    if not applications:
        print("No applications are currently tracked.")
        return

    for index, application in enumerate(applications, start=1):
        print(f"{index}. {application.company} - {application.role} [{application.status}]")


def _select_application() -> Application:
    _show_applications()
    applications = session_state["current_pipeline"]
    if not applications:
        raise ValueError("Log an application before choosing one.")

    selection = int(input("Application number: "))
    if not 1 <= selection <= len(applications):
        raise ValueError("That application number is out of range.")
    return applications[selection - 1]


def _log_application() -> None:
    company = validate_company_name(input("Company: "))
    role = input("Role: ").strip()
    if not role:
        raise ValueError("Role cannot be empty.")

    applied_text = input(f"Date applied [{date.today().isoformat()}]: ").strip()
    date_applied = date.fromisoformat(applied_text) if applied_text else date.today()
    notes = input("Notes (optional): ").strip()

    print("Proposed application:")
    print(f"  Company: {company}")
    print(f"  Role: {role}")
    print(f"  Date applied: {date_applied.isoformat()}")
    print("  Status: applied")
    print(f"  Notes: {notes or '(none)'}")
    application = log_application(company, role, date_applied, notes)
    try:
        saved = _save_pipeline()
    except Exception:
        session_state["current_pipeline"].remove(application)
        raise
    if not saved:
        session_state["current_pipeline"].remove(application)
        return
    print(f"Application logged. Suggested follow-up: {calculate_follow_up_date(application)}")


def _update_application_status() -> None:
    application = _select_application()
    statuses = ", ".join(sorted(APPLICATION_STATUSES))
    status = validate_status(input(f"New status ({statuses}): "))
    if status == application.status:
        print("Status is already set to that value; no changes made.")
        return

    previous_status = application.status
    print(f"Proposed change: {application.company} - {application.role}")
    print(f"  Status: {previous_status} -> {status}")
    update_status(application, status)
    try:
        saved = _save_pipeline()
    except Exception:
        application.status = previous_status
        raise
    if not saved:
        application.status = previous_status
        return
    print("Status updated.")


def _show_pipeline_summary() -> None:
    print("Pipeline summary:")
    for status, count in summarise_pipeline(session_state["current_pipeline"]).items():
        print(f"  {status.title():<12} {count}")


def _draft_email() -> None:
    application = _select_application()
    print("Application details to be sent to Gemini:")
    print(f"  Company: {application.company}")
    print(f"  Role: {application.role}")
    print(f"  Date applied: {application.date_applied.isoformat()}")
    print(f"  Status: {application.status}")
    if not _confirm("Send these details to Gemini to draft an email?"):
        print("No request sent.")
        return

    print("Draft follow-up email:")
    print(draft_follow_up_email(application, confirmed=True))


def main() -> None:
    try:
        session_state["current_pipeline"] = load_applications()
    except (OSError, ValueError, KeyError) as error:
        print(f"Could not load saved applications: {error}")
        return

    actions = {
        "1": ("Log an application", _log_application),
        "2": ("Update an application status", _update_application_status),
        "3": ("Display pipeline summary", _show_pipeline_summary),
        "4": ("Draft a follow-up email with Gemini", _draft_email),
    }
    while True:
        print("\nJob Application Tracker")
        for option, (label, _) in actions.items():
            print(f"{option}. {label}")
        print("5. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "5":
            return
        action = actions.get(choice)
        if action is None:
            print("Choose an option from 1 to 5.")
            continue
        try:
            action[1]()
        except (ValueError, RuntimeError, OSError) as error:
            print(f"Unable to complete that action: {error}")


if __name__ == "__main__":
    main()
