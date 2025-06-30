"""
Test script to verify README structure and links.
"""

import re
import sys


def test_readme_structure():
    """Test README.md structure and navigation links."""
    print("=== Testing README Structure ===")
    
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ README.md not found")
        return False
    
    # Test 1: Check if all navigation links have corresponding headers
    nav_links = re.findall(r'<a href="#([^"]+)">', content)
    headers = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
    
    print(f"Found {len(nav_links)} navigation links")
    print(f"Found {len(headers)} main headers")
    
    # Convert headers to link format
    header_links = []
    for header in headers:
        # Remove emojis and convert to link format
        clean_header = re.sub(r'[^\w\s-]', '', header).strip()
        link = clean_header.lower().replace(' ', '-')
        header_links.append(link)
    
    print("\nNavigation links:")
    for link in nav_links:
        print(f"  - {link}")
    
    print("\nHeader links:")
    for link in header_links:
        print(f"  - {link}")
    
    # Test 2: Check for duplicate configuration sections
    config_sections = re.findall(r'###?\s+.*[Cc]onfiguration.*', content)
    print(f"\nFound {len(config_sections)} configuration sections:")
    for section in config_sections:
        print(f"  - {section}")
    
    # Test 3: Check for multilingual mentions
    multilingual_mentions = len(re.findall(r'[Mm]ultilingual|多语言|多語言', content))
    print(f"\nMultilingual mentions: {multilingual_mentions}")
    
    # Test 4: Check table of contents completeness
    expected_sections = [
        "overview", "features", "installation", "usage", 
        "architecture", "multilingual-support", "configuration", "contributing"
    ]
    
    missing_links = []
    for expected in expected_sections:
        found = any(expected in link for link in nav_links)
        if not found:
            missing_links.append(expected)
    
    if missing_links:
        print(f"\n❌ Missing navigation links: {missing_links}")
        return False
    else:
        print("\n✅ All expected navigation links found")
    
    # Test 5: Check for redundant configuration text
    llm_config_mentions = len(re.findall(r'LLM.*[Cc]onfiguration', content))
    if llm_config_mentions > 2:
        print(f"⚠️  Possible redundant LLM configuration mentions: {llm_config_mentions}")
    else:
        print(f"✅ LLM configuration mentions: {llm_config_mentions}")
    
    print("\n✅ README structure test completed successfully!")
    return True


def test_multilingual_section():
    """Test the multilingual section specifically."""
    print("\n=== Testing Multilingual Section ===")
    
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ README.md not found")
        return False
    
    # Find multilingual section
    multilingual_section = re.search(
        r'## 🌍 Multilingual Support.*?(?=## |\Z)', 
        content, 
        re.DOTALL
    )
    
    if not multilingual_section:
        print("❌ Multilingual section not found")
        return False
    
    section_content = multilingual_section.group(0)
    
    # Check for required elements
    required_elements = [
        "Supported Languages",
        "Key Features",
        "Quick Usage",
        "Multilingual Guide"
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in section_content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Missing elements in multilingual section: {missing_elements}")
        return False
    
    # Check for supported languages
    languages = ["English", "Chinese", "Spanish", "French", "Japanese"]
    missing_languages = []
    for lang in languages:
        if lang not in section_content:
            missing_languages.append(lang)
    
    if missing_languages:
        print(f"❌ Missing languages: {missing_languages}")
        return False
    
    print("✅ Multilingual section is complete and well-structured")
    return True


def main():
    """Run all README tests."""
    print("README Structure and Content Test Suite")
    print("=" * 50)
    
    success = True
    success &= test_readme_structure()
    success &= test_multilingual_section()
    
    print("=" * 50)
    if success:
        print("🎉 All README tests passed!")
        sys.exit(0)
    else:
        print("❌ Some README tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
