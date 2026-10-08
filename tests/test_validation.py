from datetime import date
import unittest

from validation import validate_company_name, validate_deadline, validate_status


class ValidationTests(unittest.TestCase):
    def test_company_name_is_trimmed(self) -> None:
        self.assertEqual(validate_company_name("  Acme Corp  "), "Acme Corp")

    def test_empty_company_name_is_rejected(self) -> None:
        for company in ("", "   "):
            with self.subTest(company=company):
                with self.assertRaisesRegex(ValueError, "Company name cannot be empty"):
                    validate_company_name(company)

    def test_status_is_normalized(self) -> None:
        self.assertEqual(validate_status(" Interviewing "), "interviewing")

    def test_invalid_status_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Status must be one of"):
            validate_status("pending")

    def test_deadline_accepts_today_and_future_dates(self) -> None:
        today = date(2026, 10, 8)
        self.assertEqual(validate_deadline("2026-10-08", today=today), today)
        self.assertEqual(
            validate_deadline(date(2026, 10, 9), today=today), date(2026, 10, 9)
        )

    def test_past_deadline_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Deadline cannot be in the past"):
            validate_deadline("2026-10-07", today=date(2026, 10, 8))

    def test_malformed_deadline_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "valid ISO date"):
            validate_deadline("not-a-date", today=date(2026, 10, 8))


if __name__ == "__main__":
    unittest.main()
