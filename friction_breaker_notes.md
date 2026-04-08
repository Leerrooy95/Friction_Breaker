# Friction Breaker — Notes from Copilot

**From:** GitHub Copilot  
**Date:** April 8, 2026  
**Re:** Review of the previous notes, verification of findings, and changes made

---

## Summary of Changes Made

After reading the previous Copilot's notes in full and verifying each item against the live codebase and current upstream dependency/version state, the following changes were implemented:

### 1. Updated the default Claude model to `claude-sonnet-4-6`

The old default `claude-sonnet-4-20250514` was a date-pinned snapshot of Claude Sonnet 4 from May 2025. As of April 2026, Anthropic's latest model in this tier is **Claude Sonnet 4.6**, available via the alias `claude-sonnet-4-6`. The default was updated accordingly.

### 2. Added `ANTHROPIC_MODEL` environment variable override

Users can now set `ANTHROPIC_MODEL` in `.env` (or as an environment variable) to use any Claude model without editing source code. This protects against model deprecation — when Anthropic retires a model ID, users just update the env var.

Updated in: `app.py`, `.env.example`, `CLAUDE.md`

### 3. Fixed `/health` endpoint triggering GLiNER2 loading

The previous code called `_load_gliner()` inside the `/health` route, meaning every health check could trigger a ~400 MB model download on first hit. Now `/health` only reports whether GLiNER2 is **already loaded** (`_HAS_GLINER`), which is what a lightweight health check should do.

### 4. Cached taxonomy and context index

`load_taxonomy()` and `load_context_index()` previously read from disk on every `/analyze` request. Both now cache their results after the first call in module-level variables, eliminating redundant disk I/O. This has no impact on correctness for the single-user local deployment model, and improves performance if the tool is ever hosted.

### 5. Updated `peter-evans/create-pull-request` from v7 to v8

In `sync-ai-context.yml`, the action was pinned to v7. The latest stable version is v8.1.0 (released Jan 2026), which requires Actions Runner v2.327.1+ for Node 24 support. Updated to `@v8`.

### 6. Added 3 new tests (24 total, up from 21)

- `test_anthropic_model_env_override` — verifies `ANTHROPIC_MODEL` env var overrides the default
- `test_anthropic_model_default` — verifies the default model is `claude-sonnet-4-6`
- `test_health_does_not_load_gliner` — verifies `/health` does not trigger GLiNER2 loading

---

## What the Previous Notes Got Right

The previous Copilot's notes were thorough and accurate on almost every point:

- ✅ **Test coverage analysis** — Correct. 21 tests, good density, meaningful edge cases.
- ✅ **Architecture analysis** — Correct. `create_app()` pattern, lazy GLiNER loading, separated pipeline.
- ✅ **SSRF protection analysis** — Correct. DNS resolution + `ipaddress` validation is the right approach.
- ✅ **Model string expiration** — Correct and now fixed.
- ✅ **`/health` loading GLiNER2** — Correct and now fixed.
- ✅ **`load_context_index()` on every request** — Correct and now cached.
- ✅ **`_chunk_text` edge case** — Correct observation; not a bug in practice but worth documenting.
- ✅ **`output/` directory accumulation** — Correct; acceptable for local use, worth noting for hosted deployment.

### One correction: CI action versions

The notes stated that `actions/checkout@v6` and `actions/setup-python@v6` "don't exist yet." This was **incorrect as of April 2026**:

- `actions/checkout@v6` — **v6.0.2** released January 9, 2026
- `actions/setup-python@v6` — **v6.2.0** released January 21, 2026

The CI workflow was already using the correct latest major versions. No change was needed there.

---

## Items Not Changed (by Design)

| Item | Reason |
|------|--------|
| `_chunk_text` fallback | Not a bug — silent degradation on non-sentence input is acceptable since GLiNER2 wouldn't extract useful entities from structured data anyway |
| `output/` directory cleanup | Acceptable for local single-user tool. Adding cleanup logic would add complexity without clear benefit for the current use case |
| Dependency minimum versions | `flask>=3.1.3` and `requests>=2.33.0` are already correctly pinned to post-CVE-fix versions |

---

## Current State

- **24 tests passing** across the suite
- **Lint clean** (`ruff check .` — all checks passed)
- **CI workflow** uses correct latest GitHub Actions versions
- **Default model** uses current Anthropic alias (`claude-sonnet-4-6`)
- **Model override** available via `ANTHROPIC_MODEL` env var
- **Health endpoint** is fast and cheap (no model loading)
- **Taxonomy + context index** cached after first load

---

*Written April 8, 2026 by GitHub Copilot after reading the previous notes, verifying all claims, and implementing the recommended fixes.*
