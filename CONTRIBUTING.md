# Contributing to Friction Breaker

Thank you for your interest in contributing! This project aims to make democratic accountability mechanisms transparent and accessible. Contributions of all kinds are welcome.

## Ways to Contribute

### Report a New Mechanism

If you identify a mechanism (legal, regulatory, personnel, financial, or procedural) that bypasses democratic accountability and isn't already in the taxonomy:

1. Document it with verifiable sources.
2. Add it to `mechanism_classifier_taxonomy.json` following the existing format.
3. Submit a pull request.

The tool itself will also flag new mechanisms it detects (`new_mechanisms_detected` in analysis outputs) — these are candidates for addition to the taxonomy.

### Improve the Code

- Fix bugs or improve performance.
- Add tests.
- Improve the web interface.
- Enhance entity extraction or classification accuracy.

### Improve Documentation

- Clarify existing docs.
- Add usage examples.
- Translate documentation.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/Leerrooy95/Friction_Breaker.git
cd Friction_Breaker

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (including dev tools)
pip install -r requirements.txt
pip install -e ".[dev]"

# Set up your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run tests
pytest

# Run the linter
ruff check .

# Start the app
python app.py
```

## Pull Request Guidelines

1. **Fork** the repository and create your branch from `main`.
2. **Write tests** for any new functionality.
3. **Run the linter** (`ruff check .`) and fix any issues.
4. **Run tests** (`pytest`) and ensure they pass.
5. **Keep PRs focused** — one feature or fix per PR.
6. **Write clear commit messages** that explain *what* and *why*.

## Taxonomy Contribution Format

When adding a mechanism to the taxonomy JSON, include all required fields:

```json
{
  "id": "X-NN",
  "name": "Mechanism Name",
  "category": "Category Name",
  "jurisdiction": "federal | state | both",
  "mechanism_type": "legislative | regulatory | personnel | ...",
  "description": "What it does",
  "how_it_works": ["Step 1", "Step 2"],
  "durability": 5,
  "reversal_pathways": ["Countermeasure 1", "Countermeasure 2"],
  "repo_references": ["Source file or section"],
  "real_examples": ["Verified instance"],
  "status": "enacted | proposed | pending | active | challenged | active_threat"
}
```

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code. Please report unacceptable behavior via GitHub's reporting tools.

## Questions?

Open an issue or start a discussion. All good-faith contributions are appreciated.
