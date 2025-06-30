# GTPlanner API Specification

## Overview

GTPlanner provides two main REST APIs for workflow generation and design document creation, with comprehensive multilingual support and MCP integration.

## Base Configuration

- **Server**: FastAPI application
- **Host**: 0.0.0.0
- **Port**: 11211
- **MCP Port**: 8001
- **Supported Languages**: en, zh, es, fr, ja

## Authentication

Currently, no authentication is required. User identification is handled through optional `user_id` parameter for language preference storage.

## Short Planning API

### Endpoint
```
POST /planning/short
```

### Description
Generates step-by-step workflows from natural language requirements. Supports both new workflow generation and optimization of existing workflows.

### Request Body

```json
{
    "requirement": "string (required)",
    "previous_flow": "any (optional)",
    "language": "string (optional)",
    "user_id": "string (optional)"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `requirement` | string | Yes | Natural language description of the requirement |
| `previous_flow` | any | No | Existing workflow steps for optimization |
| `language` | string | No | Preferred language code (en, zh, es, fr, ja) |
| `user_id` | string | No | User identifier for language preference storage |

### Response

```json
{
    "flow": "string",
    "language": "string", 
    "user_id": "string"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `flow` | string | Generated or optimized workflow steps |
| `language` | string | Language used for processing and response |
| `user_id` | string | User identifier (if provided in request) |

### Processing Logic

1. **Input Validation**: Validates required `requirement` field
2. **Language Detection**: Determines language from input, preferences, or request
3. **Path Selection**:
   - If `previous_flow` exists: Optimization using OptimizeNode
   - If no `previous_flow`: New generation using GenerateStepsNode
4. **Localized Processing**: Uses language-specific prompt templates
5. **LLM Integration**: Calls configured LLM with localized prompts
6. **Response Generation**: Returns workflow with language metadata

### Example Requests

#### New Workflow Generation
```json
{
    "requirement": "Create a web application for task management",
    "language": "en",
    "user_id": "user123"
}
```

#### Workflow Optimization
```json
{
    "requirement": "Add user authentication feature",
    "previous_flow": ["1. Design UI", "2. Implement backend", "3. Test application"],
    "language": "en",
    "user_id": "user123"
}
```

## Long Planning API

### Endpoint
```
POST /planning/long
```

### Description
Generates comprehensive design documents based on requirements, previous workflows, and existing design documents. Produces detailed technical documentation following Node/Flow architecture patterns.

### Request Body

```json
{
    "requirement": "string (required)",
    "previous_flow": "any (optional)",
    "design_doc": "any (optional)",
    "language": "string (optional)",
    "user_id": "string (optional)"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `requirement` | string | Yes | Natural language description of the requirement |
| `previous_flow` | any | No | Previous workflow steps for context |
| `design_doc` | any | No | Existing design document for enhancement |
| `language` | string | No | Preferred language code (en, zh, es, fr, ja) |
| `user_id` | string | No | User identifier for language preference storage |

### Response

```json
{
    "flow": "string",
    "language": "string",
    "user_id": "string"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `flow` | string | Generated comprehensive design document |
| `language` | string | Language used for processing and response |
| `user_id` | string | User identifier (if provided in request) |

### Processing Logic

1. **Input Validation**: Validates required `requirement` field
2. **Context Setup**: Prepares shared context with all input parameters
3. **Requirements Analysis**: AsyncRequirementsAnalysisNode processes requirements
4. **Design Optimization**: AsyncDesignOptimizationNode generates comprehensive documentation
5. **File Output**: Saves generated documentation to `doc.md`
6. **Response Generation**: Returns design document with language metadata

### Example Request

```json
{
    "requirement": "Design a microservices architecture for e-commerce platform",
    "previous_flow": ["1. User registration", "2. Product catalog", "3. Order processing"],
    "design_doc": "# Initial Design\n## Overview\nBasic e-commerce structure...",
    "language": "en",
    "user_id": "architect001"
}
```

## Error Handling

### Common Error Responses

#### Missing Required Field
```json
{
    "error": "Missing 'requirement' in request body."
}
```

#### Invalid Language
```json
{
    "error": "Unsupported language 'de'. Supported languages: en, zh, es, fr, ja"
}
```

#### Processing Error
```json
{
    "error": "Failed to generate flow: [specific error message]"
}
```

## Multilingual Support

### Language Detection Priority
1. Explicit `language` parameter in request
2. User preference from `user_id` lookup
3. Automatic detection from `requirement` text
4. System default language (en)

### Supported Languages
- **en**: English
- **zh**: Chinese (Simplified)
- **es**: Spanish
- **fr**: French  
- **ja**: Japanese

### Language Configuration
Language preferences can be configured via:
- Environment variables (GTPLANNER_USER_{USER_ID}_LANGUAGE)
- Settings.toml configuration file
- Runtime user preference storage

## MCP Integration

### Tool: generate_flow
Maps to Short Planning API with identical parameters and response format.

### Tool: generate_design_doc  
Maps to Long Planning API with identical parameters and response format.

### MCP Server
- **Port**: 8001
- **Protocol**: HTTP streaming
- **Integration**: Direct function calls to planning APIs

## Rate Limiting

Currently no rate limiting is implemented. Consider implementing rate limiting for production deployments.

## Monitoring and Logging

- Request/response logging via FastAPI
- Language detection and selection logging
- LLM interaction logging
- Error tracking and reporting
