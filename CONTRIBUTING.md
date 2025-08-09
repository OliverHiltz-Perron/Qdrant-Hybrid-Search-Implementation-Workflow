# Contributing to FFPSA Pipeline

Thank you for your interest in contributing to the FFPSA Prevention Plan Analysis Pipeline! This document provides guidelines and instructions for contributing to the project.

## 🤝 How to Contribute

### Reporting Issues

Before creating an issue, please check if it already exists. When creating a new issue, include:

- Clear, descriptive title
- Steps to reproduce the problem
- Expected vs actual behavior
- System information (OS, Python version)
- Relevant logs or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please create an issue with:

- Clear description of the enhancement
- Use cases and benefits
- Possible implementation approach
- Any relevant examples

### Pull Requests

1. **Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/ffpsa-pipeline.git
   cd ffpsa-pipeline
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Write clean, documented code
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Run Tests**
   ```bash
   pytest tests/
   black LocalQDrant/ tests/
   flake8 LocalQDrant/ tests/
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

6. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Include screenshots if applicable

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use Black for formatting (line length: 88)
- Use type hints where appropriate
- Write docstrings for all functions and classes

Example:
```python
def process_state_data(
    state_code: str,
    task_type: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process data for a specific state and task.
    
    Args:
        state_code: Two-letter state code (e.g., "CA")
        task_type: Type of task to process
        config: Configuration dictionary
        
    Returns:
        Processed data dictionary
    """
    # Implementation here
```

### Testing

- Write tests for all new functionality
- Maintain test coverage above 80%
- Use pytest for testing
- Mock external API calls

Example test:
```python
def test_funding_source_extraction():
    """Test extraction of funding sources"""
    input_text = "Title IV-E provides $1M in funding"
    result = extract_funding_sources(input_text)
    assert len(result) > 0
    assert "Title IV-E" in result[0]["source_name"]
```

### Documentation

- Update README.md for significant changes
- Document all configuration options
- Include docstrings in code
- Add comments for complex logic

### Commit Messages

Format: `<type>: <description>`

Types:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

Examples:
- `feat: add support for batch processing`
- `fix: handle empty state data gracefully`
- `docs: update API documentation`

## 🏗️ Project Structure

```
ffpsa-pipeline/
├── LocalQDrant/          # Main pipeline code
│   ├── config/           # Configuration
│   ├── utils/            # Utilities
│   └── *.py              # Core modules
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── data/                 # Input data (gitignored)
└── docs/                 # Documentation
```

## 🔧 Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ffpsa-pipeline.git
   cd ffpsa-pipeline
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run tests**
   ```bash
   pytest tests/
   ```

## 🚀 Release Process

1. Update version in `setup.py` or `pyproject.toml`
2. Update CHANGELOG.md
3. Create release PR
4. After merge, tag release: `git tag v1.0.0`
5. Push tag: `git push origin v1.0.0`

## 📋 Checklist for Contributors

Before submitting a PR, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] PR description is clear and complete

## 🙋 Getting Help

- Check the [documentation](README.md)
- Look through existing [issues](https://github.com/yourusername/ffpsa-pipeline/issues)
- Ask questions in [discussions](https://github.com/yourusername/ffpsa-pipeline/discussions)
- Contact maintainers

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

All contributors will be recognized in the project README. Thank you for helping improve the FFPSA Pipeline!