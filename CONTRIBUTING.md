# Contributing to GTPlanner

Thank you for your interest in contributing to GTPlanner! This document provides comprehensive guidelines for contributing to our AI-powered PRD generation tool. Whether you're fixing bugs, adding features, improving documentation, or creating new nodes, we welcome your contributions.

## Before you begin

Contributions to this project must be accompanied by a Contributor License Agreement (CLA). You're required to sign the CLA when you submit your first pull request in the OpenSQZ github repositories.

You (or your employer) retain the copyright to your contribution; this simply gives us permission to use and redistribute your contributions as part of the project.

If you or your current employer have already signed the SQZ CLA (even if it was for a different project), you probably don't need to do it again.

## 🚀 Getting Started for Contributors

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10 or higher**
- **uv** (recommended) or pip for package management
- **Git** for version control
- **LLM API Access**: OpenAI-compatible API endpoint (OpenAI, Anthropic, local models, etc.)

### Development Environment Setup

1. **Fork and Clone the Repository**
   ```bash
   # Fork the repository on GitHub first, then clone your fork
   git clone https://github.com/YOUR_USERNAME/GTPlanner.git
   cd GTPlanner
   ```

2. **Set Up Development Environment**
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -r requirements.txt
   ```

3. **Set Up MCP Development Environment**
   ```bash
   cd mcp
   uv sync
   cd ..
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the project root:
   ```bash
   LLM_API_KEY=your-api-key-here
   LLM_BASE_URL=https://api.openai.com/v1
   LLM_MODEL=gpt-4
   ```

   Or configure `settings.toml`:
   ```toml
   [default.llm]
   base_url = "https://api.openai.com/v1"
   api_key = "your-api-key-here"
   model = "gpt-4"
   ```

5. **Verify Installation**
   ```bash
   # Test CLI
   uv run python main.py --help

   # Test FastAPI backend
   uv run python fastapi_main.py &
   curl http://localhost:11211/docs

   # Test MCP service
   cd mcp
   uv run python mcp_service.py &
   curl http://localhost:8001/mcp
   ```

## 🔄 Development Workflow

### Branch Naming Conventions

Use descriptive branch names that follow this pattern:
- `feature/description` - New features (e.g., `feature/add-json-output`)
- `fix/description` - Bug fixes (e.g., `fix/markdown-parsing-error`)
- `docs/description` - Documentation updates (e.g., `docs/update-api-examples`)
- `refactor/description` - Code refactoring (e.g., `refactor/async-node-structure`)
- `test/description` - Test additions/improvements (e.g., `test/add-cli-integration-tests`)

### Step-by-Step Contribution Process

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow the code standards outlined below
   - Write or update tests as needed
   - Update documentation if necessary

3. **Test Your Changes**
   ```bash
   # Run manual tests
   uv run python main.py  # Test CLI
   uv run python fastapi_main.py  # Test API
   cd mcp && uv run python mcp_service.py  # Test MCP

   # Test with sample requirements
   echo "Create a web scraping tool for e-commerce data" | uv run python main.py
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add JSON output format support"
   ```

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub. The PR template will guide you through providing all necessary information including description of changes, type of change, testing performed, and a checklist for reviewers.

### Commit Message Guidelines

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```
feat: add support for custom output templates
fix: resolve markdown parsing issue with nested lists
docs: update API documentation with new endpoints
refactor: improve async node error handling
test: add integration tests for MCP service
```

## 📝 Code Standards

### Python Code Style

- **PEP 8 Compliance**: Follow Python PEP 8 style guidelines
- **Type Hints**: Use type hints for function parameters and return values
- **Docstrings**: Use Google-style docstrings for all functions and classes
- **Async/Await**: Use async/await patterns consistently throughout the codebase

### Async Node-Based Architecture Guidelines

GTPlanner uses PocketFlow's async node-based architecture. When contributing:

1. **Node Implementation**
   ```python
   from pocketflow import AsyncNode

   class AsyncCustomNode(AsyncNode):
       async def run(self, shared_memory: dict) -> dict:
           """
           Process data asynchronously.

           Args:
               shared_memory: Shared state between nodes

           Returns:
               Updated shared memory
           """
           # Your implementation here
           return shared_memory
   ```

2. **Flow Definition**
   ```python
   from pocketflow import AsyncFlow

   flow = AsyncFlow()
   flow.add_node("input", AsyncInputNode())
   flow.add_node("process", AsyncProcessNode())
   flow.add_edge("input", "process")
   ```

3. **Error Handling**
   - Always handle exceptions gracefully
   - Log errors appropriately
   - Provide meaningful error messages to users

### File Organization

- **Core Logic**: Place main functionality in the root directory
- **Utilities**: Place helper functions in `utils/` directory
- **API**: Place API-related code in `api/` directory
- **Documentation**: Place design docs in `docs/` directory
- **Tests**: Create test files alongside the code they test

## 🧪 Testing Guidelines

### Manual Testing

Since GTPlanner doesn't currently have automated tests, thorough manual testing is essential:

#### CLI Testing
```bash
# Test interactive mode
uv run python main.py

# Test with direct input
echo "Build a REST API for user management" | uv run python main.py

# Test with markdown files
uv run python main.py --input "Enhance existing API" --files existing_docs.md
```

#### API Testing
```bash
# Start the API server
uv run python fastapi_main.py

# Test short planning endpoint
curl -X POST "http://localhost:11211/planning/short" \
  -H "Content-Type: application/json" \
  -d '{"requirement": "Create a mobile app for task management"}'

# Test long planning endpoint
curl -X POST "http://localhost:11211/planning/long" \
  -H "Content-Type: application/json" \
  -d '{"requirement": "Build an e-commerce platform", "previous_flow": "..."}'
```

#### MCP Service Testing
```bash
# Start MCP service
cd mcp
uv run python mcp_service.py

# Test with MCP client (Cherry Studio, Cursor, etc.)
# Configure MCP client with: http://127.0.0.1:8001/mcp
```

### Test Cases to Cover

When testing your changes, ensure you cover:

1. **Input Validation**
   - Empty requirements
   - Very long requirements
   - Special characters and Unicode
   - Invalid markdown files

2. **Core Functionality**
   - Requirement processing
   - Documentation generation
   - Feedback processing
   - File output

3. **Error Scenarios**
   - Network failures
   - Invalid API responses
   - File system errors
   - Configuration issues

4. **Integration Points**
   - CLI to core engine
   - API to core engine
   - MCP to planning functions

### Writing New Tests

When adding new functionality, create corresponding test scenarios:

1. **Create test files** alongside your code
2. **Document test cases** in your PR description
3. **Include edge cases** and error conditions
4. **Test async functionality** thoroughly

## 🏗️ Project Architecture Understanding

### PocketFlow-Based Architecture

GTPlanner is built on [PocketFlow](https://github.com/The-Pocket/PocketFlow), an async workflow engine. Understanding this architecture is crucial for contributors:

#### Core Concepts

1. **Nodes**: Individual processing units that perform specific tasks
2. **Flows**: Sequences of connected nodes that define the processing pipeline
3. **Shared Memory**: State that persists and is shared between nodes
4. **Async Processing**: All operations are asynchronous for better performance

#### Key Components

1. **CLI Flow** (`cli_flow.py`): Main requirement processing pipeline
2. **Short Planner Flow** (`short_planner_flow.py`): Quick planning generation
3. **Filename Flow** (`filename_flow.py`): Automatic file naming
4. **Nodes** (`nodes.py`): Core async node implementations

#### Node Types

- `AsyncInputProcessingNode`: Handles user input and markdown processing
- `AsyncRequirementsAnalysisNode`: Analyzes and categorizes requirements
- `AsyncDesignOptimizationNode`: Suggests improvements and optimizations
- `AsyncDocumentationGenerationNode`: Creates structured documentation
- `AsyncFeedbackProcessingNode`: Manages iterative refinement

### Data Flow

```
User Input → Input Processing → Requirements Analysis → Design Optimization → Documentation Generation → Feedback Processing → Output
```

## 🎯 Types of Contributions

We welcome various types of contributions:

### 1. Bug Fixes
- Fix parsing errors
- Resolve API issues
- Correct documentation generation problems
- Address configuration issues

### 2. New Features
- Additional output formats (JSON, YAML, etc.)
- New LLM provider integrations
- Enhanced CLI options
- Improved error handling

### 3. New Nodes
- Custom processing nodes
- Specialized analysis nodes
- Output formatting nodes
- Integration nodes

### 4. Utility Functions
- Enhanced markdown processing
- Better LLM communication
- Improved file handling
- Configuration management

### 5. Documentation
- Code documentation
- User guides
- API documentation
- Architecture explanations

### 6. Testing
- Integration tests
- Unit tests
- Performance tests
- End-to-end tests

### 7. Infrastructure
- CI/CD improvements
- Docker support
- Deployment scripts
- Monitoring tools

## 🐛 Issue Reporting

We use GitHub issue templates to ensure consistent and complete bug reports and feature requests. When creating a new issue:

### Bug Reports
- Use the **Bug Report** template which will guide you through providing:
  - Environment details (Python version, OS, GTPlanner version, etc.)
  - Steps to reproduce the issue
  - Expected vs actual behavior
  - Screenshots and logs if applicable

### Feature Requests
- Use the **Feature Request** template which will help you describe:
  - The problem or use case
  - Your proposed solution
  - Alternatives you've considered
  - Implementation considerations

### Creating Issues
1. Go to the [Issues page](../../issues)
2. Click "New Issue"
3. Select the appropriate template (Bug Report or Feature Request)
4. Fill out all relevant sections in the template
5. Submit your issue

The templates ensure you provide all necessary information, reducing back-and-forth and helping maintainers address your issue more quickly.

## 🔍 Review Process

### What to Expect

1. **Initial Review**: Maintainers will review your PR within 48-72 hours
2. **Feedback**: You may receive requests for changes or clarifications
3. **Testing**: Maintainers will test your changes manually
4. **Approval**: Once approved, your PR will be merged

### Review Criteria

Your contribution will be evaluated based on:

1. **Code Quality**
   - Follows project coding standards
   - Includes appropriate error handling
   - Has clear, readable code

2. **Functionality**
   - Solves the intended problem
   - Doesn't break existing functionality
   - Handles edge cases appropriately

3. **Documentation**
   - Includes necessary documentation updates
   - Has clear commit messages
   - Explains complex logic

4. **Testing**
   - Has been manually tested
   - Covers relevant test cases
   - Doesn't introduce regressions

### Addressing Review Feedback

1. **Respond Promptly**: Address feedback within a reasonable timeframe
2. **Ask Questions**: If feedback is unclear, ask for clarification
3. **Make Changes**: Update your code based on the feedback
4. **Test Again**: Ensure changes don't introduce new issues

## 💬 Communication

### Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Pull Request Comments**: For code-specific discussions

### Asking Questions

When asking questions:

1. **Search First**: Check existing issues and discussions
2. **Be Specific**: Provide context and details
3. **Include Code**: Share relevant code snippets
4. **Be Patient**: Maintainers will respond as soon as possible

### Discussion Guidelines

- Be respectful and constructive
- Stay on topic
- Help others when you can
- Follow the project's code of conduct

## 🏆 Recognition

### Contributor Recognition

We value all contributions and recognize contributors in several ways:

1. **Contributors List**: All contributors are listed in the project README
2. **Release Notes**: Significant contributions are mentioned in release notes
3. **GitHub Recognition**: Contributors are recognized through GitHub's contribution tracking

### Types of Recognition

- **Code Contributors**: Those who contribute code, tests, or documentation
- **Community Contributors**: Those who help with issues, discussions, and support
- **Documentation Contributors**: Those who improve project documentation
- **Testing Contributors**: Those who help with testing and quality assurance

### Becoming a Maintainer

Regular contributors who demonstrate:
- Consistent high-quality contributions
- Good understanding of the project
- Helpful community participation
- Reliability and commitment

May be invited to become project maintainers with additional responsibilities and privileges.

---

## 📋 Quick Reference

### Common Commands

```bash
# Development setup
git clone https://github.com/YOUR_USERNAME/GTPlanner.git
cd GTPlanner
uv sync

# Testing
uv run python main.py
uv run python fastapi_main.py
cd mcp && uv run python mcp_service.py

# Code formatting (if using black)
black .

# Type checking (if using mypy)
mypy .
```

### Project Structure Quick Reference

```
GTPlanner/
├── main.py              # CLI entry point
├── cli_flow.py          # Main processing flow
├── short_planner_flow.py # Quick planning flow
├── nodes.py             # Core async nodes
├── fastapi_main.py      # API server
├── api/v1/planning.py   # API endpoints
├── mcp/mcp_service.py   # MCP service
├── utils/               # Utility functions
└── docs/                # Documentation
```

### Key Files to Understand

- `nodes.py`: Core processing logic
- `cli_flow.py`: Main workflow definition
- `utils/call_llm.py`: LLM communication
- `api/v1/planning.py`: API implementation
- `mcp/mcp_service.py`: MCP integration

---

Thank you for contributing to GTPlanner! Your contributions help make this tool better for everyone. If you have any questions, don't hesitate to reach out through GitHub issues or discussions.