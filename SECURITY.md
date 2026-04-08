# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Friction Breaker, please report it responsibly.

### How to Report

1. **Do not** open a public GitHub issue for security vulnerabilities.
2. Email your report to the maintainer via GitHub's private vulnerability reporting feature:
   - Go to the [Security tab](https://github.com/Leerrooy95/Friction_Breaker/security) of this repository.
   - Click **"Report a vulnerability"**.
3. Include as much detail as possible:
   - A description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- Acknowledgment within **48 hours**.
- A fix or mitigation plan within **7 days** for critical issues.
- Credit in the release notes (unless you prefer to remain anonymous).

## Security Design Principles

This project follows these security principles:

- **BYOK (Bring Your Own Key)**: API keys are provided by the user and are never stored server-side. In the web interface, keys stay in the browser and are sent directly to the Anthropic API via the backend — they are not logged or persisted.
- **No data persistence**: Analysis results are saved only to the local filesystem (`output/` directory). No data is sent to third parties other than the Anthropic API for analysis.
- **Local entity extraction**: GLiNER2 runs entirely locally — no data leaves the machine for entity extraction.
- **Minimal dependencies**: The project uses a small, well-known set of dependencies to reduce supply chain risk.
