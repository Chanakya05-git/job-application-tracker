from dataclasses import dataclass
from datetime import date, timedelta
import os
from typing import Iterable, Literal, TypedDict, cast

from validation import validate_company_name, validate_status

ApplicationStatus = Literal["applied", "interviewing", "offer", "rejected", "withdrawn"]
APPLICATION_STATUS_ORDER: tuple[ApplicationStatus, ...] = (
    "applied",
    "interviewing",
    "offer",
    "rejected",
    "withdrawn",
)


@dataclass
class Application:
    company: str
    role: str
    date_applied: date
    status: ApplicationStatus = "applied"
    notes: str = ""


class SessionState(TypedDict):
    search_goal: dict[str, object] | None
    deadline: date | None
    current_pipeline: list[Application]


session_state: SessionState = {
    "search_goal": None,
    "deadline": None,
    "current_pipeline": [],
}


def log_application(
    company: str,
    role: str,
    date_applied: date | None = None,
    notes: str = "",
) -> Application:
    """Add an application to the current session pipeline."""
    if not role.strip():
        raise ValueError("Role cannot be empty.")

    application = Application(
        company=validate_company_name(company),
        role=role.strip(),
        date_applied=date_applied or date.today(),
        notes=notes.strip(),
    )
    session_state["current_pipeline"].append(application)
    return application


def update_status(application: Application, status: str) -> Application:
    """Update an application's status after validating the new value."""
    application.status = cast(ApplicationStatus, validate_status(status))
    return application


def calculate_follow_up_date(
    application: Application,
    days_after: int = 7,
) -> date:
    """Return the suggested follow-up date, seven days after applying by default."""
    if days_after < 0:
        raise ValueError("days_after cannot be negative.")
    return application.date_applied + timedelta(days=days_after)


def summarise_pipeline(
    applications: Iterable[Application],
) -> dict[ApplicationStatus, int]:
    """Count applications by status, including statuses with no applications."""
    summary = {status: 0 for status in APPLICATION_STATUS_ORDER}
    for application in applications:
        summary[application.status] += 1
    return summary


def draft_follow_up_email(
    application: Application,
    *,
    confirmed: bool = False,
    model: str = "gemini-2.5-flash",
) -> str:
    """Draft (but never send) an email using Gemini after user confirmation."""
    if not confirmed:
        raise PermissionError("Explicit confirmation is required to send details to Gemini.")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY to use Gemini email drafting.")

    try:
        from google import genai
    except ImportError as error:
        raise RuntimeError("Install the optional google-genai package to draft emails.") from error

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=(
            "Draft a concise, polite follow-up email for this job application. "
            "Do not invent facts; leave placeholders where contact details are missing. "
            "Do not send the email.\n"
            f"Company: {application.company}\n"
            f"Role: {application.role}\n"
            f"Date applied: {application.date_applied.isoformat()}\n"
            f"Status: {application.status}"
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty email draft.")
    return response.text.strip()
