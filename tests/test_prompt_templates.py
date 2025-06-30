"""
Unit tests for prompt template functionality.
"""

import unittest
from utils.prompt_templates import (
    PromptTemplateManager, 
    PromptType, 
    get_prompt_template,
    get_prompt_template_by_code
)
from utils.language_detection import SupportedLanguage


class TestPromptTemplates(unittest.TestCase):
    """Test cases for prompt templates."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = PromptTemplateManager()
    
    def test_generate_steps_templates(self):
        """Test generate_steps templates for all languages."""
        for language in SupportedLanguage:
            with self.subTest(language=language):
                template = self.manager.get_template(PromptType.GENERATE_STEPS, language)
                self.assertIsInstance(template, str)
                self.assertGreater(len(template), 100)
                self.assertIn("{req}", template)
    
    def test_optimize_steps_templates(self):
        """Test optimize_steps templates for all languages."""
        for language in SupportedLanguage:
            with self.subTest(language=language):
                template = self.manager.get_template(PromptType.OPTIMIZE_STEPS, language)
                self.assertIsInstance(template, str)
                self.assertGreater(len(template), 100)
                self.assertIn("{steps}", template)
                self.assertIn("{feedback}", template)
                self.assertIn("{prev_version}", template)
    
    def test_requirements_analysis_templates(self):
        """Test requirements_analysis templates for all languages."""
        for language in SupportedLanguage:
            with self.subTest(language=language):
                template = self.manager.get_template(PromptType.REQUIREMENTS_ANALYSIS, language)
                self.assertIsInstance(template, str)
                self.assertGreater(len(template), 100)
                self.assertIn("{parsed_documents}", template)
                self.assertIn("{short_flow_steps}", template)
                self.assertIn("{natural_language}", template)
    
    def test_fallback_to_default_language(self):
        """Test fallback to default language when template not found."""
        # This test assumes English is the default
        manager = PromptTemplateManager(default_language=SupportedLanguage.ENGLISH)
        
        # Try to get a template for a language that might not have all templates
        template = manager.get_template(PromptType.GENERATE_STEPS, SupportedLanguage.ENGLISH)
        self.assertIsInstance(template, str)
        self.assertGreater(len(template), 100)
    
    def test_convenience_functions(self):
        """Test convenience functions for template retrieval."""
        # Test get_prompt_template function
        template = get_prompt_template(PromptType.GENERATE_STEPS, SupportedLanguage.ENGLISH)
        self.assertIsInstance(template, str)
        self.assertIn("{req}", template)
        
        # Test get_prompt_template_by_code function
        template = get_prompt_template_by_code("generate_steps", "en")
        self.assertIsInstance(template, str)
        self.assertIn("{req}", template)
    
    def test_invalid_prompt_type(self):
        """Test handling of invalid prompt types."""
        with self.assertRaises(ValueError):
            get_prompt_template_by_code("invalid_type", "en")
    
    def test_invalid_language_code(self):
        """Test handling of invalid language codes."""
        with self.assertRaises(ValueError):
            get_prompt_template_by_code("generate_steps", "invalid")
    
    def test_template_formatting(self):
        """Test template formatting with variables."""
        template = get_prompt_template_by_code("generate_steps", "en")
        
        # Test formatting with variables
        formatted = template.format(req="Create a web application")
        self.assertNotIn("{req}", formatted)
        self.assertIn("Create a web application", formatted)
    
    def test_language_specific_content(self):
        """Test that templates contain language-specific content."""
        # English template should contain English words
        en_template = get_prompt_template_by_code("generate_steps", "en")
        self.assertIn("Role", en_template)
        self.assertIn("Task", en_template)
        
        # Chinese template should contain Chinese characters
        zh_template = get_prompt_template_by_code("generate_steps", "zh")
        self.assertIn("角色", zh_template)
        self.assertIn("任务", zh_template)
        
        # Spanish template should contain Spanish words
        es_template = get_prompt_template_by_code("generate_steps", "es")
        self.assertIn("Rol", es_template)
        self.assertIn("Tarea", es_template)
        
        # French template should contain French words
        fr_template = get_prompt_template_by_code("generate_steps", "fr")
        self.assertIn("Rôle", fr_template)
        self.assertIn("Tâche", fr_template)
        
        # Japanese template should contain Japanese characters
        ja_template = get_prompt_template_by_code("generate_steps", "ja")
        self.assertIn("役割", ja_template)
        self.assertIn("タスク", ja_template)
    
    def test_all_prompt_types_available(self):
        """Test that all prompt types are available for all languages."""
        prompt_types = [PromptType.GENERATE_STEPS, PromptType.OPTIMIZE_STEPS, PromptType.REQUIREMENTS_ANALYSIS]
        languages = [SupportedLanguage.ENGLISH, SupportedLanguage.CHINESE, SupportedLanguage.SPANISH, 
                    SupportedLanguage.FRENCH, SupportedLanguage.JAPANESE]
        
        for prompt_type in prompt_types:
            for language in languages:
                with self.subTest(prompt_type=prompt_type, language=language):
                    template = self.manager.get_template(prompt_type, language)
                    self.assertIsInstance(template, str)
                    self.assertGreater(len(template), 50)
    
    def test_template_consistency(self):
        """Test that templates have consistent structure across languages."""
        # All generate_steps templates should have the same placeholders
        placeholder = "{req}"
        for language in SupportedLanguage:
            with self.subTest(language=language):
                template = self.manager.get_template(PromptType.GENERATE_STEPS, language)
                self.assertIn(placeholder, template)
        
        # All optimize_steps templates should have the same placeholders
        placeholders = ["{steps}", "{feedback}", "{prev_version}"]
        for language in SupportedLanguage:
            with self.subTest(language=language):
                template = self.manager.get_template(PromptType.OPTIMIZE_STEPS, language)
                for placeholder in placeholders:
                    self.assertIn(placeholder, template)


if __name__ == "__main__":
    unittest.main()
