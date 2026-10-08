from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from storage import load_applications, save_applications
from tracker import Application


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "data" / "applications.json"
        self.application = Application(
            "Acme Corp", "Software Engineer", date(2026, 10, 1), notes="Round one"
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_load_missing_file_returns_empty_list(self) -> None:
        self.assertEqual(load_applications(self.path), [])

    def test_approval_diff_reprompts_after_vague_response(self) -> None:
        answers = iter(("maybe", "CONFIRM"))
        prompts: list[str] = []
        output: list[str] = []

        def answer(prompt: str) -> str:
            self.assertFalse(self.path.exists(), "file was written before confirmation")
            prompts.append(prompt)
            return next(answers)

        self.assertTrue(
            save_applications(
                [self.application], self.path, input_fn=answer, output_fn=output.append
            )
        )

        self.assertEqual(len(prompts), 2)
        self.assertTrue(any("Response rejected" in message for message in output))
        diff_output = "\n".join(output)
        self.assertIn(f"--- {self.path}", diff_output)
        self.assertIn(f"+++ {self.path} (proposed)", diff_output)
        self.assertIn('+    "company": "Acme Corp"', diff_output)
        self.assertEqual(load_applications(self.path), [self.application])

    def test_each_explicit_approval_word_is_accepted(self) -> None:
        for approval in ("yes", "confirm", "save"):
            with self.subTest(approval=approval):
                path = Path(self.temp_dir.name) / approval / "applications.json"
                saved = save_applications(
                    [self.application],
                    path,
                    input_fn=lambda _prompt, response=approval: response,
                    output_fn=lambda _message: None,
                )
                self.assertTrue(saved)
                self.assertEqual(load_applications(path), [self.application])

    def test_vague_input_then_cancel_leaves_existing_file_unchanged(self) -> None:
        self.path.parent.mkdir(parents=True)
        original_content = "[]\n"
        self.path.write_text(original_content, encoding="utf-8")
        answers = iter(("maybe", "no"))
        prompts: list[str] = []
        output: list[str] = []

        def answer(prompt: str) -> str:
            prompts.append(prompt)
            return next(answers)

        self.assertFalse(
            save_applications(
                [self.application], self.path, input_fn=answer, output_fn=output.append
            )
        )

        self.assertEqual(len(prompts), 2)
        self.assertEqual(self.path.read_text(encoding="utf-8"), original_content)
        self.assertTrue(any("Save cancelled" in message for message in output))

    def test_identical_content_does_not_prompt_or_rewrite(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_text("[]\n", encoding="utf-8")

        self.assertTrue(
            save_applications(
                [],
                self.path,
                input_fn=lambda _prompt: self.fail("unexpected approval prompt"),
                output_fn=lambda _message: None,
            )
        )
        self.assertEqual(self.path.read_text(encoding="utf-8"), "[]\n")


if __name__ == "__main__":
    unittest.main()
