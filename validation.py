from datetime import date

APPLICATION_STATUSES = frozenset(
    {"applied", "interviewing", "offer", "rejected", "withdrawn"}
)


def validate_company_name(company: str) -> str:
    """Return a trimmed company name, rejecting empty input."""
    if not isinstance(company, str) or not company.strip():
        raise ValueError("Company name cannot be empty.")
    return company.strip()


def validate_status(status: str) -> str:
    """Return a normalized application status or reject an unsupported value."""
    if not isinstance(status, str):
        raise ValueError("Status must be a string.")

    normalized_status = status.strip().lower()
    if normalized_status not in APPLICATION_STATUSES:
        allowed_statuses = ", ".join(sorted(APPLICATION_STATUSES))
        raise ValueError(f"Status must be one of: {allowed_statuses}.")
    return normalized_status


def validate_deadline(deadline: date | str, *, today: date | None = None) -> date:
    """Parse a deadline and reject dates before today."""
    if isinstance(deadline, str):
        try:
            deadline = date.fromisoformat(deadline)
        except ValueError as error:
            raise ValueError("Deadline must be a valid ISO date (YYYY-MM-DD).") from error
    elif not isinstance(deadline, date):
        raise ValueError("Deadline must be a date or ISO date string.")

    if deadline < (today or date.today()):
        raise ValueError("Deadline cannot be in the past.")
    return deadline
