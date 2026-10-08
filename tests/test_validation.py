import unittest
from datetime import date, timedelta

from validation import validate_company_name, validate_deadline, validate_status


class TestValidateCompanyName(unittest.TestCase):
    def test_normal_name_is_stripped(self):
        self.assertEqual(validate_company_name("  Acme Corp  "), "Acme Corp")

    def test_empty_name_rejected(self):
        with self.assertRaises(ValueError):
            validate_company_name("")

    def test_whitespace_only_rejected(self):
        with self.assertRaises(ValueError):
            validate_company_name("   ")

    def test_none_rejected(self):
        with self.assertRaises(ValueError):
            validate_company_name(None)


class TestValidateStatus(unittest.TestCase):
    def test_all_valid_statuses(self):
        for status in ("applied", "interviewing", "offer", "rejected", "withdrawn"):
            self.assertEqual(validate_status(status), status)

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            validate_status("ghosted")

    def test_empty_status_rejected(self):
        with self.assertRaises(ValueError):
            validate_status("")


class TestValidateDeadline(unittest.TestCase):
    def test_future_date_string_accepted(self):
        future = date.today() + timedelta(days=7)
        self.assertEqual(validate_deadline(future.isoformat()), future)

    def test_today_accepted(self):
        self.assertEqual(validate_deadline(date.today()), date.today())

    def test_date_object_accepted(self):
        future = date.today() + timedelta(days=3)
        self.assertEqual(validate_deadline(future), future)

    def test_past_deadline_rejected(self):
        with self.assertRaises(ValueError):
            validate_deadline((date.today() - timedelta(days=1)).isoformat())

    def test_bad_format_rejected(self):
        with self.assertRaises(ValueError):
            validate_deadline("10/08/2026")

    def test_wrong_type_rejected(self):
        with self.assertRaises(ValueError):
            validate_deadline(12345)


if __name__ == "__main__":
    unittest.main()
