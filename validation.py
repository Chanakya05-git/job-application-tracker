"""Input and data validation helpers."""

from datetime import date, datetime

from tracker import VALID_STATUSES


def validate_company_name(company: str) -> str:
    """Reject empty or whitespace-only company names."""
    if not company or not company.strip():
        raise ValueError("Company name must not be empty.")
    return company.strip()


def validate_status(status: str) -> str:
    """Reject statuses outside the allowed set."""
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status: {status!r}. Must be one of: {', '.join(VALID_STATUSES)}."
        )
    return status


def validate_deadline(deadline) -> date:
    """Reject past deadlines; accepts date, datetime, or 'YYYY-MM-DD' string."""
    if isinstance(deadline, datetime):
        deadline_date = deadline.date()
    elif isinstance(deadline, date):
        deadline_date = deadline
    elif isinstance(deadline, str):
        try:
            deadline_date = datetime.strptime(deadline.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Deadline must be in 'YYYY-MM-DD' format.")
    else:
        raise ValueError("Deadline must be a date, datetime, or 'YYYY-MM-DD' string.")

    if deadline_date < date.today():
        raise ValueError("Deadline cannot be in the past.")
    return deadline_date
