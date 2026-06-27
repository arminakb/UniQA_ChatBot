"""Tests for the package startup command."""

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


class CliTests(unittest.TestCase):
    """Startup command behavior."""

    def test_module_starts_with_env_file(self) -> None:
        with TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("LLM_API_KEY=secret-key\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, "-m", "iau_chatbot", "--env-file", str(env_file)],
                check=False,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("IAU-QA-Chatbot", result.stderr)
            self.assertNotIn("Logging error", result.stderr)
            self.assertNotIn("secret-key", result.stderr)


if __name__ == "__main__":
    unittest.main()
