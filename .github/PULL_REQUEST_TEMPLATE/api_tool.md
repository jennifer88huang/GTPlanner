# API Tool Contribution

Thank you for contributing an API tool to our intelligent tool recommendation system! Please fill out this template completely to ensure your tool meets our quality standards.

## Tool Information

**Tool ID:** `your-org.tool-name`
> Format: `organization.tool-name` (lowercase, use hyphens for spaces)

**Tool Name:** 
> Human-readable name of the tool

**Tool Type:** APIS ✅

**Summary:** 
> Brief one-line description of what this API tool does (max 100 characters)

**Category:**
- [ ] Data Processing
- [ ] Machine Learning
- [ ] Document Analysis  
- [ ] Image/Video Processing
- [ ] Text Analysis
- [ ] Database/Storage
- [ ] Communication
- [ ] Monitoring/Analytics
- [ ] Other: ___________

## Detailed Description

**Full Description:**
```
Provide a comprehensive description of the API tool, including:
- What problem it solves
- Key capabilities and features
- Target use cases
- Any limitations or requirements
```

**Key Features:**
- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

## API Specification

**Base URL:**
> e.g., `https://api.example.com/v1` (Required field: base_url)

**Authentication Required:**
- [ ] No authentication
- [ ] API Key
- [ ] OAuth 2.0
- [ ] Bearer Token
- [ ] Custom authentication

**Rate Limits:**
> Describe any rate limiting (e.g., "100 requests per minute")

### Endpoints

**Primary Endpoint:** (Required field: endpoints array)

**Method:** `POST` | `GET` | `PUT` | `DELETE`
> Required field: method

**Path:** `/endpoint-path`
> Required field: path

**Summary:**
> Brief description of what this endpoint does (Required field: summary)

**Input Schema:** (Required field: inputs)
```json
{
  "type": "object",
  "properties": {
    "parameter1": {
      "type": "string",
      "description": "Parameter description"
    },
    "parameter2": {
      "type": "number",
      "description": "Parameter description"
    }
  },
  "required": ["parameter1"]
}
```

**Output Schema:** (Required field: outputs)
```json
{
  "success_schema": {
    "type": "object",
    "properties": {
      "result": {
        "type": "string",
        "description": "Result description"
      },
      "metadata": {
        "type": "object",
        "description": "Additional metadata"
      }
    }
  }
}
```

**Additional Endpoints:** (if any)
> List other important endpoints with brief descriptions

## Usage Examples

**Example 1: Basic Usage**
```bash
curl -X POST "https://api.example.com/v1/endpoint" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "parameter1": "example_value",
    "parameter2": 42
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "result": "processed_output",
    "processing_time": "0.5s"
  }
}
```

**Example 2: Advanced Usage**
```bash
# Add another example showing more complex usage
```

## Integration Information

**Programming Language Examples:**

**Python:**
```python
import requests

response = requests.post(
    "https://api.example.com/v1/endpoint",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={"parameter1": "value"}
)
result = response.json()
```

**JavaScript:**
```javascript
const response = await fetch('https://api.example.com/v1/endpoint', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({parameter1: 'value'})
});
const result = await response.json();
```

## Testing and Validation

**Testing Completed:**
- [ ] API endpoints tested manually
- [ ] Authentication tested
- [ ] Error handling tested
- [ ] Rate limiting tested (if applicable)
- [ ] Input validation tested
- [ ] Output format verified

**Test Results:**
```
Endpoint: /endpoint-path
Method: POST
Status: 200 OK
Response Time: 0.5s
Response Format: Valid JSON ✅
```

**Error Scenarios Tested:**
- [ ] Invalid input parameters
- [ ] Missing authentication
- [ ] Rate limit exceeded
- [ ] Server errors (5xx)
- [ ] Network timeouts

## Documentation and Resources

**Official Documentation:** 
> Link to official API documentation

**API Status Page:** 
> Link to status/uptime page (if available)

**Support/Contact:** 
> How to get help with this API

**Pricing/Limits:** 
> Free tier limits, pricing information

## Quality Assurance

**API Reliability:**
- [ ] API has been stable for at least 30 days
- [ ] Uptime > 99%
- [ ] Response times < 2 seconds average
- [ ] Proper error handling and status codes

**Documentation Quality:**
- [ ] Complete API documentation available
- [ ] Clear examples provided
- [ ] Error codes documented
- [ ] Authentication process documented

**Security:**
- [ ] HTTPS only
- [ ] Proper authentication mechanisms
- [ ] No sensitive data in URLs
- [ ] Rate limiting implemented

## Maintenance and Support

**Maintenance Status:**
- [ ] Actively maintained
- [ ] Community maintained
- [ ] Stable/minimal maintenance
- [ ] Deprecated (not recommended)

**Last Updated:** YYYY-MM-DD

**Version:** 
> API version being contributed

**Breaking Changes:** 
> Any recent or planned breaking changes

## Additional Information

**Related Tools:**
> List any related or similar tools

**Dependencies:**
> Any external dependencies or requirements

**Known Issues:**
> Any known limitations or issues

**Future Plans:**
> Any planned improvements or changes

---

## Contributor Checklist

- [ ] I have tested this API thoroughly
- [ ] All required fields are completed
- [ ] Examples are working and tested
- [ ] Documentation links are valid
- [ ] API is publicly accessible
- [ ] I have permission to contribute this API information
- [ ] Tool ID follows the naming convention
- [ ] This is not a duplicate of an existing tool

## Reviewer Checklist

**For maintainers:**

- [ ] Tool ID is unique and follows naming convention
- [ ] All required information provided
- [ ] API is accessible and working
- [ ] Examples are valid and tested
- [ ] Documentation is comprehensive
- [ ] Security requirements met
- [ ] Quality standards met
- [ ] No duplicate functionality
