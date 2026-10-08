import unittest
from datetime import date, datetime, timedelta

import tracker


class TrackerTestCase(unittest.TestCase):
    def setUp(self):
        tracker.session_state["pipeline"] = []

    def tearDown(self):
        tracker.session_state["pipeline"] = []


class TestLogApplication(TrackerTestCase):
    def test_normal_log(self):
        app = tracker.log_application(
            "Acme Corp", "Software Engineer", "2026-10-01", notes="Referred"
        )
        self.assertEqual(app.company, "Acme Corp")
        self.assertEqual(app.status, "applied")
        self.assertEqual(len(tracker.session_state["pipeline"]), 1)
        self.assertEqual(app.to_dict()["notes"], "Referred")

    def test_accepts_date_object(self):
        app = tracker.log_application("Acme", "Role", date(2026, 10, 1))
        self.assertEqual(app.date_applied, "2026-10-01")

    def test_empty_company_rejected(self):
        with self.assertRaises(ValueError):
            tracker.log_application("  ", "Role", "2026-10-01")
        self.assertEqual(tracker.session_state["pipeline"], [])

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            tracker.log_application("Acme", "Role", "2026-10-01", status="ghosted")
        self.assertEqual(tracker.session_state["pipeline"], [])

    def test_bad_date_rejected(self):
        with self.assertRaises(ValueError):
            tracker.log_application("Acme", "Role", "01-10-2026")


class TestUpdateStatus(TrackerTestCase):
    def setUp(self):
        super().setUp()
        tracker.log_application("Acme", "Engineer", "2026-10-01")

    def test_normal_update(self):
        app = tracker.update_status("acme", "interviewing")
        self.assertEqual(app.status, "interviewing")

    def test_update_with_role_filter(self):
        app = tracker.update_status("Acme", "offer", role="engineer")
        self.assertEqual(app.status, "offer")

    def test_unknown_company_rejected(self):
        with self.assertRaises(ValueError):
            tracker.update_status("Nope", "offer")

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            tracker.update_status("Acme", "maybe-later")


class TestFollowUpDate(TrackerTestCase):
    def _app(self, status, applied="2026-10-01"):
        return tracker.Application("Acme", "Role", applied, status=status)

    def test_applied_follow_up(self):
        self.assertEqual(
            tracker.calculate_follow_up_date(self._app("applied")),
            date(2026, 10, 8),
        )

    def test_interviewing_follow_up(self):
        self.assertEqual(
            tracker.calculate_follow_up_date(self._app("interviewing")),
            date(2026, 10, 4),
        )

    def test_rejected_has_no_follow_up(self):
        self.assertIsNone(tracker.calculate_follow_up_date(self._app("rejected")))

    def test_bad_date_rejected(self):
        with self.assertRaises(ValueError):
            tracker.calculate_follow_up_date(self._app("applied", applied="soon"))


class TestSummarisePipeline(TrackerTestCase):
    def test_grouped_by_status(self):
        tracker.log_application("A", "R1", "2026-10-01")
        tracker.log_application("B", "R2", "2026-10-02", status="interviewing")
        summary = tracker.summarise_pipeline()
        self.assertEqual(len(summary["applied"]), 1)
        self.assertEqual(len(summary["interviewing"]), 1)
        self.assertEqual(len(summary["offer"]), 0)

    def test_format_contains_counts(self):
        tracker.log_application("A", "R1", "2026-10-01")
        text = tracker.format_pipeline_summary()
        self.assertIn("Pipeline summary (1 application(s)):", text)
        self.assertIn("[applied] (1)", text)
        self.assertIn("A — R1", text)


if __name__ == "__main__":
    unittest.main()
