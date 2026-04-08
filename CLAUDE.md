# CLAUDE.md — Developer Guide for Friction Breaker

This file provides everything needed to build, test, and run the project.

## Quick Setup

```bash
# 1. Clone
git clone https://github.com/Leerrooy95/Friction_Breaker.git
cd Friction_Breaker

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install all dependencies (app + dev tools)
pip install -e ".[dev]"

# 4. Set your Anthropic API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# 5. Run
python app.py
# Open http://localhost:5000
```

## Commands

| Task             | Command              |
|------------------|----------------------|
| Run the app      | `python app.py`      |
| Run tests        | `pytest`             |
| Run linter       | `ruff check .`       |
| Auto-fix lint    | `ruff check . --fix` |
| CLI analysis     | `python app.py --analyze "text here"` |
| Analyze a URL    | `python app.py --url "https://..."` |
| Custom port      | `python app.py --port 8080` |

## Project Layout

```
app.py                              # Flask app + CLI + full analysis pipeline
mechanism_classifier_taxonomy.json  # 54 mechanisms, 8 categories
templates/index.html                # Web UI (single-page)
tests/test_app.py                   # Test suite (pytest)
_AI_CONTEXT_INDEX/                  # Background research context files
pyproject.toml                      # Project metadata, deps, tool config
requirements.txt                    # Pip requirements (mirrors pyproject.toml)
```

## Architecture

1. **User inputs text** (paste, URL, or CLI)
2. **GLiNER2** extracts entities locally (zero-cost, runs on CPU, ~400 MB model)
3. **Mechanism Classifier** matches entities against the 54-mechanism taxonomy
4. **Claude API** generates countermeasure analysis (uses the user's own key)
5. **Results** are returned as JSON and displayed in the web UI

## Key Conventions

- **BYOK**: API keys are user-provided. Never stored server-side. Never logged.
- **Python ≥ 3.10** required. Tested on 3.10, 3.11, 3.12, 3.13.
- **Ruff** for linting. Config is in `pyproject.toml`. Line length 120.
- **No data persistence**: analysis results only saved to local `output/` directory.
- **SSRF protection**: URL fetching blocks private/internal addresses, non-HTTP schemes, and follows no redirects.

## Dependencies

| Package         | Purpose                                  |
|-----------------|------------------------------------------|
| `flask`         | Web server + REST API                    |
| `anthropic`     | Claude API client (mechanism analysis)   |
| `gliner`        | Local entity extraction (GLiNER2 model)  |
| `python-dotenv` | Load `.env` file for API key config      |
| `requests`      | URL fetching for article analysis        |
| `pytest`        | Test runner (dev)                        |
| `ruff`          | Linter (dev)                             |

## CI

GitHub Actions runs on every push/PR to `main`:
- **Lint** — `ruff check .`
- **Test** — `pytest tests/ -v` across Python 3.10–3.13
- **Security** — `pip-audit` for dependency vulnerability scanning

Dependabot monitors both pip and GitHub Actions dependencies weekly.

## Adding a New Mechanism

1. Add the entry to `mechanism_classifier_taxonomy.json` following the existing schema.
2. Required fields: `id`, `name`, `category`, `description`, `durability`, `reversal_pathways`.
3. Run `pytest` to verify the taxonomy still validates.
4. See `MECHANISM_CLASSIFIER_README.md` for full taxonomy documentation.
