"""Persistence layer for tracked data."""

import difflib
import json
from pathlib import Path
from typing import List

DATA_FILE = Path(__file__).parent / "data" / "applications.json"

# Words that count as explicit approval; anything else is rejected.
APPROVAL_WORDS = {"yes", "confirm", "save"}
CANCEL_WORDS = {"no", "n", "cancel", "abort"}


def load_applications() -> List[dict]:
    """Load saved application records, or an empty list if none exist."""
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _render(applications: List[dict]) -> str:
    return json.dumps(applications, indent=2) + "\n"


def _build_diff(old: List[dict], new: List[dict]) -> str:
    diff = difflib.unified_diff(
        _render(old).splitlines(keepends=True),
        _render(new).splitlines(keepends=True),
        fromfile=f"{DATA_FILE} (current)",
        tofile=f"{DATA_FILE} (proposed)",
    )
    return "".join(diff)


def request_save_approval(applications: List[dict], prompt_fn=input) -> bool:
    """Show the exact diff and require an explicit approval word.

    Vague responses like "maybe" are rejected and the user is re-prompted.
    Returns True only on "yes"/"confirm"/"save"; False on explicit cancel.
    """
    existing: List[dict] = []
    if DATA_FILE.exists():
        try:
            existing = load_applications()
        except (json.JSONDecodeError, OSError):
            existing = []

    diff = _build_diff(existing, applications)
    if diff.strip():
        print("\nProposed changes:")
        print(diff)
    else:
        print("\nNo changes relative to the saved file.")

    while True:
        answer = prompt_fn(
            'Type "yes", "confirm", or "save" to approve ("no"/"cancel" to abort): '
        ).strip().lower()
        if answer in APPROVAL_WORDS:
            return True
        if answer in CANCEL_WORDS:
            return False
        print(
            f'Rejected: "{answer}" is not an explicit confirmation. '
            'Please type "yes", "confirm", or "save", or "no"/"cancel" to abort.'
        )


def save_applications(applications: List[dict], *, prompt_fn=input) -> bool:
    """Write application records after the interactive approval gate."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not request_save_approval(applications, prompt_fn=prompt_fn):
        print("Cancelled — data/applications.json left unchanged.")
        return False
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(_render(applications))
    return True
