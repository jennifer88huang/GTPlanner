"""
Unit tests for language detection functionality.
"""

import unittest

from utils.language_detection import (
    LanguageDetector,
    SupportedLanguage,
    detect_language,
    get_supported_languages,
    is_supported_language,
)


class TestLanguageDetection(unittest.TestCase):
    """Test cases for language detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = LanguageDetector()

    def test_english_detection(self):
        """Test English language detection."""
        test_cases = [
            "Hello world, this is a test",
            "Create a web application for e-commerce",
            "The quick brown fox jumps over the lazy dog",
            "I need to build a mobile app with React Native",
        ]

        for text in test_cases:
            with self.subTest(text=text):
                result = self.detector.detect_language(text)
                self.assertEqual(result, SupportedLanguage.ENGLISH)

    def test_chinese_detection(self):
        """Test Chinese language detection."""
        test_cases = [
            "你好世界",
            "创建一个网站应用程序",
            "我需要构建一个移动应用",
            "这是一个测试文本",
        ]

        for text in test_cases:
            with self.subTest(text=text):
                result = self.detector.detect_language(text)
                self.assertEqual(result, SupportedLanguage.CHINESE)

    def test_spanish_detection(self):
        """Test Spanish language detection."""
        test_cases = [
            "Hola mundo, cómo estás",
            "Crear una aplicación web para el negocio",
            "Necesito construir una aplicación móvil con características especiales",
            "Este es un texto de prueba en español",
        ]

        for text in test_cases:
            with self.subTest(text=text):
                result = self.detector.detect_language(text)
                self.assertEqual(result, SupportedLanguage.SPANISH)

    def test_french_detection(self):
        """Test French language detection."""
        test_cases = [
            "Bonjour le monde",
            "Créer une application web",
            "J'ai besoin de construire une application mobile",
            "Ceci est un texte de test",
        ]

        for text in test_cases:
            with self.subTest(text=text):
                result = self.detector.detect_language(text)
                self.assertEqual(result, SupportedLanguage.FRENCH)

    def test_japanese_detection(self):
        """Test Japanese language detection."""
        test_cases = [
            "こんにちは世界",
            "ウェブアプリケーションを作成する",
            "モバイルアプリを構築する必要があります",
            "これはテストテキストです",
        ]

        for text in test_cases:
            with self.subTest(text=text):
                result = self.detector.detect_language(text)
                self.assertEqual(result, SupportedLanguage.JAPANESE)

    def test_user_preference_override(self):
        """Test that user preference overrides detection."""
        english_text = "Hello world"

        # Without preference, should detect English
        result = self.detector.detect_language(english_text)
        self.assertEqual(result, SupportedLanguage.ENGLISH)

        # With Chinese preference, should use Chinese
        result = self.detector.detect_language(english_text, user_preference="zh")
        self.assertEqual(result, SupportedLanguage.CHINESE)

    def test_empty_input_fallback(self):
        """Test fallback for empty input."""
        result = self.detector.detect_language("")
        self.assertEqual(result, self.detector.default_language)

        result = self.detector.detect_language("   ")
        self.assertEqual(result, self.detector.default_language)

    def test_invalid_preference_ignored(self):
        """Test that invalid user preferences are ignored."""
        text = "Hello world"
        result = self.detector.detect_language(text, user_preference="invalid")
        self.assertEqual(result, SupportedLanguage.ENGLISH)

    def test_supported_language_validation(self):
        """Test supported language validation."""
        # Valid languages
        valid_languages = ["en", "zh", "es", "fr", "ja"]
        for lang in valid_languages:
            with self.subTest(lang=lang):
                self.assertTrue(is_supported_language(lang))

        # Invalid languages
        invalid_languages = ["de", "ru", "invalid", ""]
        for lang in invalid_languages:
            with self.subTest(lang=lang):
                self.assertFalse(is_supported_language(lang))

    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        supported = get_supported_languages()
        expected = ["en", "zh", "es", "fr", "ja"]
        self.assertEqual(sorted(supported), sorted(expected))

    def test_convenience_function(self):
        """Test the convenience detect_language function."""
        result = detect_language("Hello world")
        self.assertEqual(result, "en")

        result = detect_language("你好世界")
        self.assertEqual(result, "zh")

    def test_chinese_vs_japanese_disambiguation(self):
        """Test disambiguation between Chinese and Japanese."""
        # Pure Chinese (no hiragana/katakana)
        chinese_text = "创建网站应用程序"
        result = self.detector.detect_language(chinese_text)
        self.assertEqual(result, SupportedLanguage.CHINESE)

        # Japanese with hiragana
        japanese_text = "ウェブアプリケーションを作成します"
        result = self.detector.detect_language(japanese_text)
        self.assertEqual(result, SupportedLanguage.JAPANESE)

        # Japanese with hiragana and kanji
        japanese_mixed = "これは日本語のテストです"
        result = self.detector.detect_language(japanese_mixed)
        self.assertEqual(result, SupportedLanguage.JAPANESE)

    def test_language_name_retrieval(self):
        """Test getting human-readable language names."""
        test_cases = [
            ("en", "English"),
            ("zh", "中文"),
            ("es", "Español"),
            ("fr", "Français"),
            ("ja", "日本語"),
            ("invalid", "Unknown"),
        ]

        for code, expected_name in test_cases:
            with self.subTest(code=code):
                name = self.detector.get_language_name(code)
                self.assertEqual(name, expected_name)


if __name__ == "__main__":
    unittest.main()
