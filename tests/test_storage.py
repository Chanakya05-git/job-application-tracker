import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import storage


class StorageTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.tmpdir.name) / "applications.json"
        self._original_data_file = storage.DATA_FILE
        storage.DATA_FILE = self.data_file

    def tearDown(self):
        storage.DATA_FILE = self._original_data_file
        self.tmpdir.cleanup()

    def _prompts(self, answers):
        """Return a prompt_fn that records calls and yields the given answers."""
        calls = []
        remaining = list(answers)

        def fake_input(prompt=""):
            calls.append(prompt)
            return remaining.pop(0)

        fake_input.calls = calls
        return fake_input


class TestLoadApplications(StorageTestCase):
    def test_missing_file_returns_empty(self):
        self.assertEqual(storage.load_applications(), [])

    def test_existing_file_loaded(self):
        records = [{"company": "Acme", "role": "Eng", "date_applied": "2026-10-01",
                    "status": "applied", "notes": ""}]
        self.data_file.write_text(json.dumps(records), encoding="utf-8")
        self.assertEqual(storage.load_applications(), records)


class TestApprovalGate(StorageTestCase):
    def test_explicit_yes_saves(self):
        prompts = self._prompts(["yes"])
        ok = storage.save_applications([{"company": "Acme"}], prompt_fn=prompts)
        self.assertTrue(ok)
        self.assertEqual(json.loads(self.data_file.read_text()), [{"company": "Acme"}])

    def test_confirm_and_save_words_accepted(self):
        for word in ("confirm", "save"):
            self.data_file.unlink(missing_ok=True)
            prompts = self._prompts([word])
            self.assertTrue(storage.save_applications([{"x": 1}], prompt_fn=prompts))

    def test_vague_maybe_rejected_and_reprompted(self):
        prompts = self._prompts(["maybe", "yes"])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            ok = storage.save_applications([{"company": "Acme"}], prompt_fn=prompts)
        self.assertTrue(ok)
        self.assertEqual(len(prompts.calls), 2)
        self.assertIn("Rejected", out.getvalue())

    def test_vague_then_cancel_writes_nothing(self):
        prompts = self._prompts(["maybe", "no"])
        ok = storage.save_applications([{"company": "Acme"}], prompt_fn=prompts)
        self.assertFalse(ok)
        self.assertEqual(len(prompts.calls), 2)
        self.assertFalse(self.data_file.exists())

    def test_cancel_word_aborts(self):
        for word in ("no", "cancel"):
            prompts = self._prompts([word])
            self.assertFalse(storage.save_applications([{"x": 1}], prompt_fn=prompts))
            self.assertFalse(self.data_file.exists())

    def test_diff_shown_before_saving(self):
        self.data_file.write_text(json.dumps([{"company": "Old"}]), encoding="utf-8")
        prompts = self._prompts(["yes"])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            storage.save_applications([{"company": "New"}], prompt_fn=prompts)
        printed = out.getvalue()
        self.assertIn('"company": "Old"', printed)
        self.assertIn('"company": "New"', printed)


if __name__ == "__main__":
    unittest.main()
