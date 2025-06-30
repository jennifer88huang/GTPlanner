# GTPlanner Multilingual Support Guide

GTPlanner now supports multiple languages, providing a seamless planning experience for users regardless of their preferred language. This guide explains how to use and configure the multilingual features.

## Supported Languages

GTPlanner currently supports the following languages:

| Language | Code | Native Name |
|----------|------|-------------|
| English  | `en` | English     |
| Chinese  | `zh` | 中文        |
| Spanish  | `es` | Español     |
| French   | `fr` | Français    |
| Japanese | `ja` | 日本語      |

## Features

### 1. Automatic Language Detection

GTPlanner can automatically detect the language of user input using advanced pattern matching:

- **Chinese**: Detects Chinese characters (Simplified and Traditional)
- **Japanese**: Detects Hiragana, Katakana, and Kanji characters
- **Spanish**: Detects Spanish-specific words and characters (ñ, á, é, etc.)
- **French**: Detects French-specific words and characters (à, ç, é, etc.)
- **English**: Default detection for Latin script content

### 2. Language Priority System

The system determines the language to use based on the following priority order:

1. **Explicit Request Language**: Language specified in API request
2. **User Preference**: Stored user language preference
3. **Automatic Detection**: Language detected from user input
4. **Default Language**: Fallback to configured default (usually English)

### 3. Localized Prompt Templates

All system prompts are available in multiple languages with culturally appropriate content:

- **Generate Steps**: Workflow generation prompts
- **Optimize Steps**: Workflow optimization prompts  
- **Requirements Analysis**: Requirements analysis prompts

### 4. Fallback Mechanism

If a requested language is not supported, the system automatically falls back to:
1. The configured default language
2. English as the final fallback

## Configuration

### Settings File Configuration

Add multilingual settings to your `settings.toml`:

```toml
[default.multilingual]
# Default language for the system (en, zh, es, fr, ja)
default_language = "en"
# Enable automatic language detection from user input
auto_detect = true
# Fallback to default language when requested language is not supported
fallback_enabled = true
# Supported languages (can be customized to enable/disable specific languages)
supported_languages = ["en", "zh", "es", "fr", "ja"]
```

### Environment Variables

You can also configure multilingual settings using environment variables:

```bash
# Default language
GTPLANNER_DEFAULT_LANGUAGE=en

# Enable/disable auto-detection
GTPLANNER_AUTO_DETECT=true

# Enable/disable fallback
GTPLANNER_FALLBACK_ENABLED=true

# Supported languages (comma-separated)
GTPLANNER_SUPPORTED_LANGUAGES=en,zh,es,fr,ja

# User-specific language preferences
GTPLANNER_USER_LANGUAGE=zh
GTPLANNER_USER_ALICE_LANGUAGE=es
```

## API Usage

### Short Planning with Language Support

```python
import requests

# Explicit language specification
response = requests.post("/planning/short", json={
    "requirement": "Create a web application",
    "language": "en",
    "user_id": "user123"
})

# Auto-detection (Chinese input)
response = requests.post("/planning/short", json={
    "requirement": "创建一个网站应用",
    "user_id": "user123"
})

# Response includes language information
{
    "flow": "1. Design: Create application architecture...",
    "language": "en",
    "user_id": "user123"
}
```

### Long Planning with Language Support

```python
# Long planning with language specification
response = requests.post("/planning/long", json={
    "requirement": "Crear una aplicación web completa",
    "previous_flow": "...",
    "language": "es",
    "user_id": "user456"
})
```

## MCP Tool Usage

The MCP tools now support multilingual functionality:

### Generate Flow Tool

```python
# Using the MCP tool with language support
result = await generate_flow(
    requirement="Build a mobile app",
    language="en",
    user_id="developer1"
)

# Auto-detection example
result = await generate_flow(
    requirement="モバイルアプリを作成する",
    user_id="developer2"
)
```

### Generate Design Document Tool

```python
# Generate design document in Spanish
result = await generate_design_doc(
    requirement="Crear documentación técnica",
    previous_flow="...",
    language="es",
    user_id="architect1"
)
```

## Language Detection Examples

### Input Examples and Expected Detection

```python
# English
"Create a web application for e-commerce" → "en"

# Chinese
"创建一个电子商务网站应用" → "zh"

# Spanish  
"Crear una aplicación web para comercio electrónico" → "es"

# French
"Créer une application web pour le commerce électronique" → "fr"

# Japanese
"eコマース用のWebアプリケーションを作成する" → "ja"
```

## Best Practices

### 1. Language Consistency

- Use consistent language throughout a conversation/session
- Store user language preferences for better experience
- Provide language selection options in your UI

### 2. Fallback Handling

- Always handle potential language fallbacks gracefully
- Inform users when their preferred language isn't available
- Provide clear language selection options

### 3. Cultural Considerations

- Prompts are adapted for cultural context in each language
- Technical terminology is localized appropriately
- Communication styles match cultural expectations

### 4. Testing

- Test with native speakers of each supported language
- Verify that technical content is accurate in all languages
- Test edge cases and mixed-language inputs

## Troubleshooting

### Common Issues

1. **Language Not Detected Correctly**
   - Ensure input text has sufficient content for detection
   - Use explicit language parameter for short inputs
   - Check if the language is in the supported list

2. **Fallback Not Working**
   - Verify `fallback_enabled` is set to `true`
   - Check that default language is properly configured
   - Ensure English templates are available as final fallback

3. **Configuration Not Loading**
   - Verify `settings.toml` file exists and is properly formatted
   - Check environment variable names and values
   - Ensure dynaconf is properly installed

### Debug Mode

Enable debug logging to troubleshoot language detection:

```python
import logging
logging.getLogger('utils.multilingual_utils').setLevel(logging.DEBUG)
```

## Extending Language Support

To add support for a new language:

1. Add the language to `SupportedLanguage` enum in `utils/language_detection.py`
2. Add detection patterns for the language
3. Create prompt templates for all prompt types
4. Update configuration files
5. Add tests for the new language
6. Update documentation

## Performance Considerations

- Language detection is fast and lightweight
- Prompt templates are cached for performance
- Fallback mechanisms add minimal overhead
- Consider caching user language preferences

## Security Notes

- Language detection doesn't store or log user input
- User language preferences should be stored securely
- Validate language codes to prevent injection attacks
- Sanitize user input before language detection
