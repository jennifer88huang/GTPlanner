"""
Test script for multilingual functionality in GTPlanner.

This script tests various aspects of the multilingual system including:
- Language detection
- Prompt template selection
- Fallback mechanisms
- API endpoint functionality
"""

import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.v1.planning import ShortPlanningRequest, short_planning
from utils.config_manager import get_default_language, is_auto_detect_enabled
from utils.language_detection import (
    detect_language,
    get_supported_languages,
    is_supported_language,
)
from utils.multilingual_utils import (
    determine_language,
    get_localized_prompt,
    validate_language_request,
)


async def test_language_detection():
    """Test language detection functionality."""
    print("=== Testing Language Detection ===")

    test_cases = [
        ("Hello, I need to create a web application", "en"),
        ("你好，我需要创建一个网站应用", "zh"),
        ("Hola, necesito crear una aplicación web", "es"),
        ("Bonjour, j'ai besoin de créer une application web", "fr"),
        ("こんにちは、ウェブアプリケーションを作成する必要があります", "ja"),
    ]

    for text, expected_lang in test_cases:
        detected = detect_language(text)
        print(f"Text: {text[:50]}...")
        print(f"Expected: {expected_lang}, Detected: {detected}")
        print(f"Match: {'✓' if detected == expected_lang else '✗'}")
        print()


def test_supported_languages():
    """Test supported language validation."""
    print("=== Testing Supported Languages ===")

    supported = get_supported_languages()
    print(f"Supported languages: {supported}")

    test_languages = ["en", "zh", "es", "fr", "ja", "de", "invalid"]

    for lang in test_languages:
        is_supported = is_supported_language(lang)
        print(
            f"Language '{lang}': {'✓ Supported' if is_supported else '✗ Not supported'}"
        )
    print()


async def test_prompt_templates():
    """Test prompt template retrieval."""
    print("=== Testing Prompt Templates ===")

    languages = ["en", "zh", "es", "fr", "ja"]

    # Test generate_steps templates
    print("\nTesting generate_steps:")
    for lang in languages:
        try:
            prompt = get_localized_prompt(
                "generate_steps", lang, req="Test requirement"
            )
            print(f"  {lang}: ✓ Template retrieved ({len(prompt)} chars)")
        except Exception as e:
            print(f"  {lang}: ✗ Error - {e}")

    # Test optimize_steps templates
    print("\nTesting optimize_steps:")
    for lang in languages:
        try:
            prompt = get_localized_prompt(
                "optimize_steps",
                lang,
                steps="1. Step one\n2. Step two",
                feedback="Add step three",
                prev_version=1,
            )
            print(f"  {lang}: ✓ Template retrieved ({len(prompt)} chars)")
        except Exception as e:
            print(f"  {lang}: ✗ Error - {e}")

    # Test requirements_analysis templates
    print("\nTesting requirements_analysis:")
    for lang in languages:
        try:
            prompt = get_localized_prompt(
                "requirements_analysis",
                lang,
                parsed_documents="Sample document",
                short_flow_steps="1. Analysis\n2. Design",
                natural_language="Test requirement",
            )
            print(f"  {lang}: ✓ Template retrieved ({len(prompt)} chars)")
        except Exception as e:
            print(f"  {lang}: ✗ Error - {e}")
    print()


def test_fallback_mechanism():
    """Test fallback to default language."""
    print("=== Testing Fallback Mechanism ===")

    # Test with unsupported language
    try:
        prompt = get_localized_prompt("generate_steps", "unsupported", req="Test")
        print("✓ Fallback mechanism works - got prompt despite unsupported language")
    except Exception as e:
        print(f"✗ Fallback failed: {e}")

    # Test validation
    valid_cases = ["en", "zh", "es"]
    invalid_cases = ["de", "ru", "invalid"]

    for lang in valid_cases:
        is_valid, message = validate_language_request(lang)
        print(f"Language '{lang}': {'✓' if is_valid else '✗'} {message}")

    for lang in invalid_cases:
        is_valid, message = validate_language_request(lang)
        print(f"Language '{lang}': {'✓' if is_valid else '✗'} {message}")
    print()


def test_configuration():
    """Test configuration management."""
    print("=== Testing Configuration ===")

    default_lang = get_default_language()
    auto_detect = is_auto_detect_enabled()

    print(f"Default language: {default_lang}")
    print(f"Auto-detection enabled: {auto_detect}")
    print()


async def test_api_endpoints():
    """Test API endpoints with multilingual support."""
    print("=== Testing API Endpoints ===")

    test_cases = [
        {
            "requirement": "Create a simple web application",
            "language": "en",
            "description": "English request",
        },
        {
            "requirement": "创建一个简单的网站应用",
            "language": "zh",
            "description": "Chinese request",
        },
        {
            "requirement": "Crear una aplicación web simple",
            "language": "es",
            "description": "Spanish request",
        },
        {
            "requirement": "Create a web app",
            "language": None,
            "description": "Auto-detect language",
        },
    ]

    for i, case in enumerate(test_cases):
        print(f"\nTest case {i+1}: {case['description']}")
        try:
            request = ShortPlanningRequest(
                requirement=case["requirement"],
                language=case["language"],
                user_id=f"test_user_{i}",
            )

            result = await short_planning(request)

            if "error" in result:
                print(f"  ✗ Error: {result['error']}")
            else:
                flow = result.get("flow", "")
                response_lang = result.get("language", "unknown")
                print(f"  ✓ Success - Response language: {response_lang}")
                print(f"  Flow length: {len(flow)} characters")

        except Exception as e:
            print(f"  ✗ Exception: {e}")
    print()


def test_language_determination():
    """Test the language determination logic."""
    print("=== Testing Language Determination ===")

    test_cases = [
        {
            "user_input": "Hello world",
            "user_preference": None,
            "request_language": None,
            "expected": "en",
            "description": "Auto-detect English",
        },
        {
            "user_input": "Hello world",
            "user_preference": "zh",
            "request_language": None,
            "expected": "zh",
            "description": "User preference overrides detection",
        },
        {
            "user_input": "Hello world",
            "user_preference": "zh",
            "request_language": "es",
            "expected": "es",
            "description": "Request language has highest priority",
        },
        {
            "user_input": "",
            "user_preference": None,
            "request_language": None,
            "expected": "en",
            "description": "Default language when no input",
        },
    ]

    for case in test_cases:
        result = determine_language(
            case["user_input"], case["user_preference"], case["request_language"]
        )

        match = result == case["expected"]
        print(f"{case['description']}: {'✓' if match else '✗'}")
        print(f"  Expected: {case['expected']}, Got: {result}")
    print()


async def main():
    """Run all tests."""
    print("GTPlanner Multilingual Functionality Test Suite")
    print("=" * 50)

    # Run all tests
    await test_language_detection()
    test_supported_languages()
    await test_prompt_templates()
    test_fallback_mechanism()
    test_configuration()
    test_language_determination()
    await test_api_endpoints()

    print("=" * 50)
    print("Test suite completed!")


if __name__ == "__main__":
    asyncio.run(main())
