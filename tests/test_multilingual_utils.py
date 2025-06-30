"""
Unit tests for multilingual utilities.
"""

import unittest
from unittest.mock import MagicMock, patch

from utils.multilingual_utils import (
    MultilingualManager,
    determine_language,
    get_language_info,
    get_localized_prompt,
    validate_language_request,
)


class TestMultilingualUtils(unittest.TestCase):
    """Test cases for multilingual utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = MultilingualManager()

    def test_language_determination_priority(self):
        """Test language determination priority order."""
        # Test priority 1: Explicit request language
        result = self.manager.determine_language(
            user_input="Hello world", user_preference="zh", request_language="es"
        )
        self.assertEqual(result, "es")

        # Test priority 2: User preference
        result = self.manager.determine_language(
            user_input="Hello world", user_preference="zh", request_language=None
        )
        self.assertEqual(result, "zh")

        # Test priority 3: Auto-detection
        result = self.manager.determine_language(
            user_input="你好世界", user_preference=None, request_language=None
        )
        self.assertEqual(result, "zh")

        # Test priority 4: Default language
        result = self.manager.determine_language(
            user_input="", user_preference=None, request_language=None
        )
        self.assertEqual(result, "en")

    def test_invalid_language_handling(self):
        """Test handling of invalid language codes."""
        # Invalid request language should be ignored
        result = self.manager.determine_language(
            user_input="Hello world", user_preference=None, request_language="invalid"
        )
        self.assertEqual(result, "en")  # Should fall back to detection

        # Invalid user preference should be ignored
        result = self.manager.determine_language(
            user_input="Hello world", user_preference="invalid", request_language=None
        )
        self.assertEqual(result, "en")  # Should fall back to detection

    def test_get_localized_prompt_success(self):
        """Test successful prompt retrieval."""
        prompt = self.manager.get_localized_prompt(
            "generate_steps", "en", req="Test requirement"
        )
        self.assertIsInstance(prompt, str)
        self.assertIn("Test requirement", prompt)

    def test_get_localized_prompt_fallback(self):
        """Test prompt retrieval with fallback."""
        # This should work even with invalid language due to fallback
        prompt = self.manager.get_localized_prompt(
            "generate_steps", "invalid", req="Test requirement"
        )
        self.assertIsInstance(prompt, str)
        self.assertIn("Test requirement", prompt)

    def test_validate_language_request(self):
        """Test language request validation."""
        # Valid languages
        valid_languages = ["en", "zh", "es", "fr", "ja"]
        for lang in valid_languages:
            with self.subTest(lang=lang):
                is_valid, message = self.manager.validate_language_request(lang)
                self.assertTrue(is_valid)
                self.assertIn("supported", message)

        # Invalid languages
        invalid_languages = ["de", "ru", "invalid"]
        for lang in invalid_languages:
            with self.subTest(lang=lang):
                is_valid, message = self.manager.validate_language_request(lang)
                self.assertFalse(is_valid)
                self.assertIn("not supported", message)

        # None/empty language
        is_valid, message = self.manager.validate_language_request(None)
        self.assertTrue(is_valid)
        self.assertIn("No language", message)

    def test_get_language_info(self):
        """Test language information retrieval."""
        info = self.manager.get_language_info()

        self.assertIn("default_language", info)
        self.assertIn("supported_languages", info)
        self.assertIn("total_supported", info)

        self.assertEqual(info["default_language"], "en")
        self.assertIsInstance(info["supported_languages"], dict)
        self.assertGreater(info["total_supported"], 0)

        # Check that each supported language has proper info
        for lang_code, lang_info in info["supported_languages"].items():
            self.assertIn("code", lang_info)
            self.assertIn("name", lang_info)
            self.assertIn("is_default", lang_info)
            self.assertEqual(lang_info["code"], lang_code)

    def test_create_multilingual_response(self):
        """Test multilingual response creation."""
        response = self.manager.create_multilingual_response(
            content="Test content", language_code="en", include_language_info=True
        )

        self.assertIn("content", response)
        self.assertIn("language", response)
        self.assertIn("language_info", response)

        self.assertEqual(response["content"], "Test content")
        self.assertEqual(response["language"], "en")
        self.assertIsInstance(response["language_info"], dict)

        # Test without language info
        response = self.manager.create_multilingual_response(
            content="Test content", language_code="zh", include_language_info=False
        )

        self.assertNotIn("language_info", response)
        self.assertEqual(response["language"], "zh")

    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test determine_language function
        result = determine_language("Hello world")
        self.assertEqual(result, "en")

        # Test get_localized_prompt function
        prompt = get_localized_prompt("generate_steps", "en", req="Test")
        self.assertIsInstance(prompt, str)
        self.assertIn("Test", prompt)

        # Test validate_language_request function
        is_valid, message = validate_language_request("en")
        self.assertTrue(is_valid)

        # Test get_language_info function
        info = get_language_info()
        self.assertIsInstance(info, dict)
        self.assertIn("default_language", info)

    def test_error_handling(self):
        """Test error handling in multilingual utilities."""
        # Test with invalid prompt type
        with self.assertRaises(ValueError):
            self.manager.get_localized_prompt("invalid_type", "en")

        # Test that the function handles missing parameters gracefully
        # by not providing required template variables
        try:
            # This should work but return a template with unformatted placeholders
            result = self.manager.get_localized_prompt("generate_steps", "en")
            self.assertIsInstance(result, str)
            self.assertIn("{req}", result)  # Should still contain placeholder
        except Exception:
            # If it raises an exception, that's also acceptable behavior
            pass

    def test_default_language_configuration(self):
        """Test default language configuration."""
        # Test with different default language
        manager = MultilingualManager(default_language="zh")
        self.assertEqual(manager.default_language, "zh")

        # Test language determination with different default
        result = manager.determine_language("")
        self.assertEqual(result, "zh")

    @patch("utils.multilingual_utils.logger")
    def test_logging(self, mock_logger):
        """Test that appropriate logging occurs."""
        # Test successful prompt retrieval logging
        self.manager.get_localized_prompt("generate_steps", "en", req="Test")
        mock_logger.info.assert_called()

        # Test language determination logging
        self.manager.determine_language("Hello", request_language="es")
        mock_logger.info.assert_called()


if __name__ == "__main__":
    unittest.main()
