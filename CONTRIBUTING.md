# Contributing to AI Voice Detection API

First off, thank you for considering contributing to AI Voice Detection! 🎉

It's people like you that make this project such a great tool.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

---

## 📜 Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## 🤔 How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

**When reporting a bug, include:**
- Clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Python version, OS, and other environment details
- Relevant logs or error messages

### 💡 Suggesting Features

Feature suggestions are welcome! Please:
- Check if the feature already exists or is planned
- Provide a clear use case
- Describe the expected behavior
- Consider backward compatibility

### 🔧 Code Contributions

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

---

## 🛠️ Development Setup

### Prerequisites

- Python 3.10+
- Git
- FFmpeg
- Docker (optional)

### Step-by-Step Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/ai-voice-detection.git
cd ai-voice-detection

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# 4. Install pre-commit hooks
pre-commit install

# 5. Run the development server
uvicorn app_main:app --reload

# 6. Run tests to verify setup
pytest
```

### Project Structure

```
ai-voice-detection/
├── app/                    # Application package
│   ├── __init__.py
│   ├── config.py          # Configuration
│   ├── models.py          # Pydantic models
│   ├── audio_processor.py # Audio processing
│   ├── classifier.py      # ML classifier
│   └── auth.py            # Authentication
├── tests/                  # Test suite
├── docs/                   # Documentation
├── models/                 # ML models
├── app_main.py            # FastAPI app
├── train_model.py         # Model training
└── requirements.txt       # Dependencies
```

---

## 🎨 Code Style

We follow strict code style guidelines to maintain consistency.

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [isort](https://pycqa.github.io/isort/) for imports
- Maximum line length: 100 characters

### Formatting Commands

```bash
# Format code with Black
black .

# Sort imports
isort .

# Check style without modifying
black --check .
isort --check-only .

# Run linter
flake8 .

# Type checking
mypy app/
```

### Type Hints

All functions should have type hints:

```python
# ✅ Good
def process_audio(audio_bytes: bytes, language: str) -> dict:
    ...

# ❌ Bad
def process_audio(audio_bytes, language):
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def detect_voice(audio: np.ndarray, sr: int) -> tuple[str, float]:
    """
    Detect if voice is AI-generated or human.
    
    Args:
        audio: Audio signal as numpy array
        sr: Sample rate
        
    Returns:
        tuple: (prediction, confidence)
        
    Raises:
        ValueError: If audio is too short
        
    Example:
        >>> prediction, confidence = detect_voice(audio, 22050)
        >>> print(f"{prediction}: {confidence:.2%}")
    """
```

---

## 📝 Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/) format.

### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, semicolons) |
| `refactor` | Code change that neither fixes bug nor adds feature |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |
| `ci` | CI/CD changes |

### Examples

```bash
# Feature
git commit -m "feat(api): add batch processing endpoint"

# Bug fix
git commit -m "fix(audio): handle empty audio files gracefully"

# Documentation
git commit -m "docs: update API examples in README"

# Breaking change
git commit -m "feat(api)!: change response format for /detect endpoint

BREAKING CHANGE: Response now includes 'metadata' field"
```

---

## 🔀 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass (`pytest`)
- [ ] Added tests for new features
- [ ] Updated documentation if needed
- [ ] No merge conflicts with `main`

### PR Title Format

Use conventional commit format:
```
feat(component): brief description
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe testing approach

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed the code
- [ ] Added necessary documentation
- [ ] Tests pass locally
```

### Review Process

1. Submit PR against `main` branch
2. Automated checks run (tests, linting)
3. Reviewer assigned within 48 hours
4. Address feedback
5. Approval and merge

---

## 🐛 Reporting Bugs

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Ubuntu 22.04]
 - Python: [e.g. 3.10.5]
 - Version: [e.g. 1.0.0]

**Additional context**
Any other context about the problem.
```

---

## 💡 Suggesting Features

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want.

**Describe alternatives you've considered**
Other solutions you've thought about.

**Additional context**
Any other context or screenshots.
```

---

## 🏆 Recognition

Contributors are recognized in:
- README.md contributors section
- CHANGELOG.md release notes
- GitHub releases

---

## ❓ Questions?

- Open a [Discussion](https://github.com/yourusername/ai-voice-detection/discussions)
- Join our [Discord](https://discord.gg/example)
- Email: contributors@example.com

---

Thank you for contributing! 🙏
