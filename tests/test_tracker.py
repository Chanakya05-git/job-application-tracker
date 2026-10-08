from datetime import date
import unittest

from tracker import (
    Application,
    calculate_follow_up_date,
    log_application,
    session_state,
    summarise_pipeline,
    update_status,
)


class TrackerTests(unittest.TestCase):
    def setUp(self) -> None:
        session_state["current_pipeline"].clear()

    def tearDown(self) -> None:
        session_state["current_pipeline"].clear()

    def test_log_application_trims_fields_and_adds_to_pipeline(self) -> None:
        application = log_application(
            "  Acme Corp  ", "  Software Engineer  ", date(2026, 10, 1), "  Follow up  "
        )

        self.assertEqual(application.company, "Acme Corp")
        self.assertEqual(application.role, "Software Engineer")
        self.assertEqual(application.notes, "Follow up")
        self.assertEqual(application.status, "applied")
        self.assertEqual(session_state["current_pipeline"], [application])

    def test_log_application_rejects_empty_company_or_role(self) -> None:
        with self.assertRaisesRegex(ValueError, "Company name cannot be empty"):
            log_application("   ", "Engineer")
        with self.assertRaisesRegex(ValueError, "Role cannot be empty"):
            log_application("Acme Corp", "  ")
        self.assertEqual(session_state["current_pipeline"], [])

    def test_update_status_normalizes_and_rejects_invalid_status(self) -> None:
        application = Application("Acme Corp", "Engineer", date(2026, 10, 1))

        self.assertIs(update_status(application, " Interviewing "), application)
        self.assertEqual(application.status, "interviewing")
        with self.assertRaisesRegex(ValueError, "Status must be one of"):
            update_status(application, "pending")
        self.assertEqual(application.status, "interviewing")

    def test_calculate_follow_up_date(self) -> None:
        application = Application("Acme Corp", "Engineer", date(2026, 10, 1))

        self.assertEqual(calculate_follow_up_date(application), date(2026, 10, 8))
        self.assertEqual(calculate_follow_up_date(application, days_after=0), date(2026, 10, 1))
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            calculate_follow_up_date(application, days_after=-1)

    def test_summarise_pipeline_includes_empty_statuses(self) -> None:
        applications = [
            Application("Acme Corp", "Engineer", date(2026, 10, 1)),
            Application("Globex", "Analyst", date(2026, 10, 2), status="offer"),
        ]

        summary = summarise_pipeline(applications)

        self.assertEqual(summary["applied"], 1)
        self.assertEqual(summary["offer"], 1)
        self.assertEqual(summary["interviewing"], 0)
        self.assertEqual(sum(summary.values()), 2)


if __name__ == "__main__":
    unittest.main()
