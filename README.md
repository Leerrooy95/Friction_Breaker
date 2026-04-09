# 🔧 Friction Breaker

**Mechanism Classifier + Countermeasure Engine**

[![CI](https://github.com/Leerrooy95/Friction_Breaker/actions/workflows/ci.yml/badge.svg)](https://github.com/Leerrooy95/Friction_Breaker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An open-source tool that identifies legal, regulatory, and procedural mechanisms used to bypass democratic accountability — and generates ranked countermeasures that citizens, legislators, and courts can implement.

Powered by [The Regulated Friction Project](https://github.com/Leerrooy95/The_Regulated_Friction_Project).

---

## Why This Exists

Governments and institutions use complex legal, regulatory, personnel, and financial mechanisms to concentrate power and reduce public oversight. These mechanisms are often buried in dense legislation, regulatory filings, and executive orders that most people never read — and wouldn't understand if they did.

Friction Breaker makes these mechanisms visible. It reads any text you give it, identifies the specific accountability-bypassing mechanisms at play, and explains in plain English what they mean and what can be done about them — ranked by how durable each countermeasure is (hardest to undo first).

---

## What It Does

1. **You paste text** — a news article, executive order, bill text, regulatory action, or anything else.
2. **GLiNER2 extracts entities** locally (zero-cost, no API needed, runs on CPU).
3. **The Mechanism Classifier** matches what it finds against a taxonomy of **56 documented mechanisms** across 8 categories, extracted from The Regulated Friction Project.
4. **Claude generates countermeasure analysis** — ranked by durability (hardest to reverse first) — in plain English anyone can understand.

Every analysis includes:
- **Which mechanisms** are being used and how they work
- **Specific countermeasures** for each mechanism, ranked by durability
- **Who can act** — citizens, state legislatures, Congress, or courts
- **A plain-English summary** written at an 8th-grade reading level

**No data is stored on any server. Your API key goes directly to Anthropic. This tool is fully open source.**

---

## Quick Start

### Prerequisites

- Python 3.10 or later
- An [Anthropic API key](https://console.anthropic.com/) (for the Claude analysis step)

### Installation

```bash
# Clone
git clone https://github.com/Leerrooy95/Friction_Breaker.git
cd Friction_Breaker

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set your API key
cp .env.example .env
# Edit .env → add your ANTHROPIC_API_KEY

# Run
python app.py
# Open http://localhost:5000
```

### CLI Mode

```bash
# Analyze text directly
python app.py --analyze "The Arkansas PSC approved Entergy's application despite finding the cost not reasonable..."

# Analyze a URL
python app.py --url "https://example.com/article-about-new-regulation"

# Batch mode: process a file of URLs/texts (one per line)
python app.py --batch inputs.txt

# Custom port
python app.py --port 8080
```

---

## BYOK (Bring Your Own Key)

This tool requires an **Anthropic API key** for the countermeasure analysis step. You can:

1. Enter it in the web interface (stays in your browser, sent directly to Anthropic)
2. Set it in `.env` as `ANTHROPIC_API_KEY=sk-ant-...`
3. Export it: `export ANTHROPIC_API_KEY=sk-ant-...`

GLiNER2 runs entirely locally — no API key needed for entity extraction.

---

## How It Works

```
New text input (news article, executive order, legislative text, etc.)
    ↓
GLiNER2 entity extraction (local, zero-cost)
    ↓
Mechanism Classifier (matches against 54-mechanism taxonomy)
    ↓
Claude API analysis (user's own key)
    ↓
Countermeasure Report (plain English, ranked by durability)
```

### The Mechanism Taxonomy

Each mechanism in the taxonomy has:

| Field               | Description                                                              |
|---------------------|--------------------------------------------------------------------------|
| **ID**              | Unique identifier (e.g., A-01)                                          |
| **Category**        | Legislative Architecture, Regulatory Capture, Personnel Cycling, etc.   |
| **Durability**      | 1–10 score (how resistant to reversal)                                  |
| **Reversal Pathways** | Specific countermeasures ranked by durability                         |
| **Real Examples**   | Verified instances from the research                                    |

**8 categories, 56 mechanisms.** See [`MECHANISM_CLASSIFIER_README.md`](MECHANISM_CLASSIFIER_README.md) for full documentation.

---

## Stack

| Component              | What It Does                                          | Cost  |
|------------------------|-------------------------------------------------------|-------|
| **GLiNER2**            | Local entity extraction (205M params, runs on CPU)    | Free  |
| **Claude API**         | Mechanism classification + countermeasure analysis     | BYOK  |
| **Flask**              | Web interface + REST API                               | Free  |
| **Mechanism Taxonomy** | 56 mechanisms from The Regulated Friction Project      | Free  |

---

## Project Structure

```
Friction_Breaker/
├── app.py                              # Flask app + CLI + analysis pipeline
├── mechanism_classifier_taxonomy.json  # Mechanism taxonomy (56 mechanisms, 8 categories)
├── MECHANISM_CLASSIFIER_README.md      # Taxonomy documentation
├── templates/
│   └── index.html                      # Web UI
├── _AI_CONTEXT_INDEX/                  # Background knowledge base
├── output/                             # Analysis results (auto-created, gitignored)
├── tests/                              # Test suite
├── requirements.txt                    # Python dependencies
├── pyproject.toml                      # Modern Python project metadata
├── .env.example                        # API key template
├── CLAUDE.md                           # Developer quick-start guide
├── .github/
│   ├── workflows/ci.yml                # CI pipeline (lint + test + security audit)
│   └── dependabot.yml                  # Automated dependency updates
├── CONTRIBUTING.md                     # How to contribute
├── CODE_OF_CONDUCT.md                  # Community standards
├── SECURITY.md                         # Vulnerability reporting policy
├── LICENSE                             # MIT License
└── README.md                           # This file
```

---

## Syncing the Knowledge Base

The `_AI_CONTEXT_INDEX/` directory contains background research context from [The Regulated Friction Project](https://github.com/Leerrooy95/The_Regulated_Friction_Project). To update:

```bash
git clone https://github.com/Leerrooy95/The_Regulated_Friction_Project.git /tmp/rfp
cp /tmp/rfp/_AI_CONTEXT_INDEX/*.md _AI_CONTEXT_INDEX/
```

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run the linter
ruff check .

# Run tests
pytest

# Start development server
python app.py
```

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

The most impactful contribution is **adding new mechanisms to the taxonomy**. The tool itself flags mechanisms it detects that aren't in the taxonomy (`new_mechanisms_detected` in analysis outputs) — these are candidates for addition.

---

## Security

- **BYOK (Bring Your Own Key)**: Your API key is never stored or logged. In the web UI it stays in your browser; the backend sends it directly to Anthropic per-request.
- **No data persistence**: Results are saved only to your local `output/` directory. Nothing is sent to third parties beyond the Anthropic API.
- **Local entity extraction**: GLiNER2 runs entirely on your machine — no text leaves your computer for entity extraction.
- **SSRF protection**: The URL-fetching feature blocks requests to private/internal addresses, metadata endpoints, and non-HTTP schemes.
- **Minimal dependencies**: The project uses a small, well-known set of packages with automated vulnerability monitoring via Dependabot and pip-audit.

See [SECURITY.md](SECURITY.md) for the vulnerability reporting policy.

---

## License

[MIT License](LICENSE) — same as [The Regulated Friction Project](https://github.com/Leerrooy95/The_Regulated_Friction_Project).

---

## Changelog

### v1.1.0 (April 2026)
- **Batch mode**: `--batch` CLI flag processes a file of URLs/texts (one per line), saving all results to `output/`
- **Configurable rate limiting**: `RATE_LIMIT` environment variable (default: `10 per minute`)
- **Context index in Claude prompt**: Background research from `_AI_CONTEXT_INDEX/` is now included in analysis prompts (capped at 8K chars)
- **Taxonomy version tracking**: `/health` endpoint and analysis metadata now include `taxonomy_version`
- **Taxonomy v2.2.0**: 56 mechanisms across 8 categories (docs updated to match)

---

Built by [Austin Smith](https://github.com/Leerrooy95) · Leroy's Web Development
