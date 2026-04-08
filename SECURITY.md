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
- **SSRF protection**: URL fetching blocks private/internal addresses, non-HTTP schemes, and re-validates the destination IP at every redirect hop before following it. Redirects are limited to 5 hops.
- **Rate limiting**: The `/analyze` endpoint is rate-limited (10 requests per minute per IP) to prevent quota exhaustion.

## Known Limitations

### DNS Rebinding (TOCTOU)

The SSRF protection resolves DNS and validates the resulting IP *before* each request. However, the underlying `requests` library performs its own independent DNS resolution when opening the connection. A malicious DNS server with a TTL-0 record could theoretically return a public IP for the validation step and a private IP for the connection step. This is a classic DNS time-of-check/time-of-use (TOCTOU) gap.

**Practical impact:** Exploitation requires a controlled DNS server and precise timing. The risk is negligible for local/single-user usage. If you intend to deploy Friction Breaker as a shared or public-facing service, consider adding a custom `requests` transport adapter that pins the resolved IP, or run the application behind a network-layer firewall that blocks outbound traffic to RFC 1918 addresses.
