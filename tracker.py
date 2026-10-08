"""Core tracking logic."""

import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

VALID_STATUSES = ("applied", "interviewing", "offer", "rejected", "withdrawn")

# How long after the application date to follow up, per status.
FOLLOW_UP_WINDOWS = {
    "applied": timedelta(days=7),
    "interviewing": timedelta(days=3),
    "offer": timedelta(days=7),
    "rejected": None,
    "withdrawn": None,
}

session_state = {
    "search_goals": {
        "target_role_type": None,
        "target_company_size": None,
        "applications_per_week": None,
        "weekly_hours_available": None,
    },
    "deadline": None,
    "pipeline": [],
}


@dataclass
class Application:
    """A single job application in the pipeline."""

    company: str
    role: str
    date_applied: str  # ISO date string, e.g. "2026-10-08"
    status: str = "applied"
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "company": self.company,
            "role": self.role,
            "date_applied": self.date_applied,
            "status": self.status,
            "notes": self.notes,
        }


def log_application(
    company: str,
    role: str,
    date_applied,
    status: str = "applied",
    notes: str = "",
) -> Application:
    """Validate and add a new application to the pipeline."""
    from validation import validate_company_name, validate_status

    company = validate_company_name(company)
    status = validate_status(status)

    if isinstance(date_applied, datetime):
        date_applied = date_applied.date().isoformat()
    elif isinstance(date_applied, date):
        date_applied = date_applied.isoformat()
    else:
        try:
            datetime.strptime(str(date_applied).strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError("date_applied must be in 'YYYY-MM-DD' format.")
        date_applied = str(date_applied).strip()

    app = Application(
        company=company,
        role=role,
        date_applied=date_applied,
        status=status,
        notes=notes,
    )
    session_state["pipeline"].append(app)
    return app


def update_status(company: str, new_status: str, role: Optional[str] = None) -> Application:
    """Update the status of a matching application in the pipeline."""
    from validation import validate_company_name, validate_status

    company = validate_company_name(company)
    new_status = validate_status(new_status)

    for app in session_state["pipeline"]:
        if app.company.lower() == company.lower() and (
            role is None or app.role.lower() == role.lower()
        ):
            app.status = new_status
            return app
    raise ValueError(f"No application found for company: {company}")


def calculate_follow_up_date(application: Application) -> Optional[date]:
    """Return the follow-up date for an application, or None if not applicable."""
    window = FOLLOW_UP_WINDOWS.get(application.status)
    if window is None:
        return None
    try:
        applied = datetime.strptime(application.date_applied, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(
            f"date_applied must be in 'YYYY-MM-DD' format, got {application.date_applied!r}"
        )
    return applied + window


def summarise_pipeline() -> Dict[str, List[Application]]:
    """Group pipeline applications by status."""
    summary: Dict[str, List[Application]] = {status: [] for status in VALID_STATUSES}
    for app in session_state["pipeline"]:
        summary.setdefault(app.status, []).append(app)
    return summary


def format_pipeline_summary() -> str:
    """Return a human-readable summary grouped by status."""
    summary = summarise_pipeline()
    total = sum(len(apps) for apps in summary.values())
    lines = [f"Pipeline summary ({total} application(s)):"]
    for status, apps in summary.items():
        lines.append(f"\n[{status}] ({len(apps)})")
        if apps:
            for app in apps:
                lines.append(f"  - {app.company} — {app.role} (applied {app.date_applied})")
        else:
            lines.append("  (none)")
    return "\n".join(lines)


def draft_follow_up_email(application: Application, model_name: str = "gemini-1.5-flash") -> str:
    """Draft a follow-up email using the Gemini API (optional helper).

    Requires the 'google-generativeai' package and a GEMINI_API_KEY
    environment variable. Raises RuntimeError with setup instructions
    if either is missing.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError(
            "Gemini support requires the 'google-generativeai' package. "
            "Install it with: pip install google-generativeai"
        )

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Export it before using this helper."
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    prompt = (
        "Write a short, professional follow-up email for a job application.\n"
        f"Company: {application.company}\n"
        f"Role: {application.role}\n"
        f"Date applied: {application.date_applied}\n"
        f"Current status: {application.status}\n"
        f"Notes: {application.notes or 'None'}\n"
        "Keep it under 120 words and polite. Include a subject line."
    )
    response = model.generate_content(prompt)
    return response.text
