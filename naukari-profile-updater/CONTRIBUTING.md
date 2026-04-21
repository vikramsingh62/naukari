# Contributing to Naukari Profile Auto-Updater

Thank you for your interest in contributing! Here's how you can help:

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/naukari-profile-updater.git`
3. Create a new branch: `git checkout -b feature/my-feature`

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Install dev dependencies
pip install pylint black pytest pytest-cov
```

## Code Style

- Follow PEP 8
- Use black for formatting: `black src/ config/ tests/`
- Use isort for imports: `isort src/ config/ tests/`
- Run pylint: `pylint src/ config/ tests/`

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_automator.py::TestNaukariAutomator::test_initialization -v
```

## Making Changes

1. Make sure your code passes tests
2. Update documentation if needed
3. Add tests for new features
4. Commit with clear messages: `git commit -m "Add feature: description"`

## Submitting a Pull Request

1. Push to your fork
2. Create a Pull Request with a clear title and description
3. Reference any related issues: `Fixes #123`
4. Wait for CI checks to pass
5. Address review comments

## Testing Against Naukari.com

- **Do NOT commit credentials**
- Use environment variables or `.env` for testing
- Test on a personal account first
- Document any changes to selectors or page structure

## Reporting Issues

Please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)
- Python version and OS
- Full error logs

## Questions?

- Check existing issues and discussions
- Create a new discussion for questions
- Review the README for common troubleshooting

Thank you for contributing! 🎉
