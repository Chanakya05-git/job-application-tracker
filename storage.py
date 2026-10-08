from difflib import unified_diff
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Callable, Iterable

from tracker import Application
from validation import validate_status

DATA_FILE = Path(__file__).parent / "data" / "applications.json"


def load_applications(path: Path = DATA_FILE) -> list[Application]:
    """Load application records, returning an empty list when no file exists."""
    if not path.exists():
        return []

    with path.open(encoding="utf-8") as data_file:
        records = json.load(data_file)

    return [
        Application(
            company=record["company"],
            role=record["role"],
            date_applied=date.fromisoformat(record["date_applied"]),
            status=validate_status(record["status"]),
            notes=record.get("notes", ""),
        )
        for record in records
    ]


def save_applications(
    applications: Iterable[Application],
    path: Path = DATA_FILE,
    *,
    input_fn: Callable[[str], str] | None = None,
    output_fn: Callable[[str], None] | None = None,
) -> bool:
    """Show the exact file diff and save only after explicit user approval."""
    records = []
    for application in applications:
        record = asdict(application)
        record["date_applied"] = application.date_applied.isoformat()
        records.append(record)

    proposed_content = json.dumps(records, indent=2) + "\n"
    existing_content = path.read_text(encoding="utf-8") if path.exists() else ""
    if existing_content == proposed_content:
        (output_fn or print)(f"No changes to save in {path}.")
        return True

    diff = "".join(
        unified_diff(
            existing_content.splitlines(keepends=True),
            proposed_content.splitlines(keepends=True),
            fromfile=str(path),
            tofile=f"{path} (proposed)",
        )
    )
    write = output_fn or print
    prompt = input_fn or input
    write(f"Proposed changes to {path}:")
    write(diff)

    while True:
        response = prompt("Save these changes? Type yes, confirm, or save (or no to cancel): ")
        answer = response.strip().lower()
        if answer in {"yes", "confirm", "save"}:
            break
        if answer in {"no", "n", "cancel"}:
            write("Save cancelled; no file changes made.")
            return False
        write("Response rejected. Enter yes, confirm, or save; use no or cancel to abort.")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(proposed_content, encoding="utf-8")
    write(f"Saved applications to {path}.")
    return True
