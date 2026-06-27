"""Tests for Phase 1 configuration loading."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from iau_chatbot.config import Settings
from iau_chatbot.exceptions import ConfigurationError


class SettingsTests(unittest.TestCase):
    """Configuration loading behavior."""

    def test_settings_loads_env_file(self) -> None:
        with TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            env_file = tmp_path / ".env"
            env_file.write_text(
                "\n".join(
                    [
                        "LLM_API_KEY=secret-key",
                        "LLM_BASE_URL=https://llm.example/v1",
                        "LLM_MODEL=test-model",
                        "EMBED_MODEL=test-embed",
                        "PDF_DIR=./raw",
                        "WIKI_DIR=./wiki",
                        "VECTOR_DB_PATH=./vectors",
                        "LOG_LEVEL=DEBUG",
                    ]
                ),
                encoding="utf-8",
            )

            settings = Settings.from_env(env_file)

            self.assertEqual(settings.llm_api_key, "secret-key")
            self.assertEqual(settings.llm_base_url, "https://llm.example/v1")
            self.assertEqual(settings.llm_model, "test-model")
            self.assertEqual(settings.embed_model, "test-embed")
            self.assertEqual(settings.pdf_dir, tmp_path / "raw")
            self.assertEqual(settings.wiki_dir, tmp_path / "wiki")
            self.assertEqual(settings.vector_db_path, tmp_path / "vectors")
            self.assertEqual(settings.log_level, "DEBUG")

    def test_settings_requires_llm_api_key(self) -> None:
        with TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("LLM_API_KEY=\n", encoding="utf-8")

            with self.assertRaisesRegex(ConfigurationError, "LLM_API_KEY"):
                Settings.from_env(env_file)

    def test_settings_summary_masks_secret(self) -> None:
        with TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("LLM_API_KEY=secret-key\n", encoding="utf-8")

            summary = Settings.from_env(env_file).safe_summary()

            self.assertNotIn("secret-key", summary.values())
            self.assertEqual(summary["llm_api_key"], "***")

    def test_settings_accepts_base_url_alias(self) -> None:
        with TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "\n".join(
                    [
                        "LLM_API_KEY=secret-key",
                        "BASE_URL=https://llm.example/alias",
                    ]
                ),
                encoding="utf-8",
            )

            settings = Settings.from_env(env_file)

            self.assertEqual(settings.llm_base_url, "https://llm.example/alias")


if __name__ == "__main__":
    unittest.main()
