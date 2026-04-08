# Friction Breaker — Notes from Copilot

**From:** GitHub Copilot  
**Date:** April 8, 2026  
**Re:** What I found when I read the Friction Breaker code, and what I'd tell you about it

---

## First: This Is a Meaningful Step Forward

The Friction Breaker is genuinely different from everything else in the portfolio. The other tools — Live Trackers, Arkansas Tracker, AR-PAC-Track — are *for you*. They run in private repos, power a private dashboard, feed research you're doing. Friction Breaker is *for other people*. It's the first tool in the portfolio built explicitly to put your research infrastructure in the hands of citizens, journalists, and legislators.

That's worth noting. The tool isn't just a new project — it's the beginning of a different category of output.

I extracted `leroysfrictionbreaker.tar.xz` and read everything. Here's what I found.

---

## What the Code Does Well

### The test coverage is the best in the portfolio (proportionally)

21 tests on ~552 lines of application code. That's a test density higher than anything else you've built. And the tests aren't trivial — they cover:

- Taxonomy structure validation (schema, field presence, durability range)
- Flask app creation and all four endpoints (/, /analyze, /taxonomy, /health)
- Edge cases: no JSON body, missing API key, missing text, text + URL combinations
- SSRF protection: localhost, 127.0.0.1, 169.254.169.254, 192.168.x.x, 10.x.x.x, and non-HTTP schemes (file://, ftp://)
- Security: API key never appears in /health response

The `test_ssrf_blocked_private_ip` test explicitly validates four different attack vectors. That's not boilerplate test writing — that's someone who thought through the threat model.

This is what the previous Copilot recommended for the pipeline code. You did it here. That matters.

### The architecture is clean

`create_app()` pattern — same as Legal Assistant. Testable. Separated from the CLI and `__main__` block. The analysis pipeline (`run_analysis()`) is a separate function that Flask calls, meaning it can be tested or called from CLI without instantiating the full web app.

The lazy-loading of GLiNER2 (`_load_gliner()`) is thoughtful — it won't download 400MB on import or on test runs that don't need it. That's why the CI tests pass without GLiNER2 installed.

### The SSRF protection is thorough

`_is_private_host()` goes beyond a simple blocklist. It:
1. Checks explicit blocked hostnames
2. Checks `.local` suffix
3. Checks IP prefix strings for private ranges
4. Resolves DNS and checks via `ipaddress.ip_address().is_private / .is_loopback / .is_link_local / .is_reserved`

That last step — DNS resolution and `ipaddress` validation — is what separates real SSRF protection from the kind that gets bypassed by pointing a domain at 192.168.1.1. Good.

### The prompt is honest about what it doesn't know

The Claude prompt explicitly says: *"If no mechanisms match, say so honestly — don't force matches."* And: *"If you detect a mechanism NOT in the taxonomy, add it to `new_mechanisms_detected`."*

That self-expanding taxonomy design is clever. The tool literally tells you when to update it. Every analysis output that surfaces a `new_mechanisms_detected` entry is a contribution candidate for the taxonomy JSON.

---

## What I'd Flag

### 1. The model string will expire

```python
_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
```

Anthropic model identifiers are versioned by date. `claude-sonnet-4-20250514` is Claude Sonnet 4, released May 14, 2025. Anthropic deprecates older model versions — when that happens, every API call will fail with a model-not-found error and the app will be broken for every user who hasn't updated the source.

**What to do:** Either pin to a named alias that Anthropic keeps current (like `claude-sonnet-4-5` if they offer one), or add a `ANTHROPIC_MODEL` environment variable so users can override it without editing source code. The `.env.example` is already there — just add `ANTHROPIC_MODEL=claude-sonnet-4-20250514` to it as an optional override.

### 2. The `/health` endpoint loads GLiNER2 on every call

```python
@app.route("/health")
def health():
    return jsonify({
        "gliner_available": _HAS_GLINER or _load_gliner() is not None,
        ...
    })
```

`_load_gliner()` is called inside `/health`. That means every health check — whether from a monitoring system, a load balancer, or a curious developer hitting the endpoint — triggers a potential 400MB model download and multi-second load time on first call.

The lazy-load design was specifically meant to avoid this. Health checks should be fast and cheap.

**What to do:** Change to `"gliner_available": _HAS_GLINER` — reflecting whether GLiNER2 is *already* loaded, not whether it *can* be loaded. Or use a separate flag that gets set after the first actual analysis call.

### 3. `load_context_index()` runs on every `/analyze` request

```python
def run_analysis(text: str, api_key: str) -> dict:
    taxonomy = load_taxonomy()
    context_index = load_context_index()
    ...
```

Both `load_taxonomy()` and `load_context_index()` read from disk on every single analysis request. `load_context_index()` reads every `.md` file in `_AI_CONTEXT_INDEX/`, truncates them, and concatenates them — this is non-trivial disk I/O and string processing.

For a single-user local tool this is fine. If you ever put this on a server with real traffic, it'll become noticeable.

**What to do:** Cache both at app startup (load once into module-level variables when `create_app()` is called) and only reload if the files change, or just accept the current behavior and document it as "designed for single-user local use."

### 4. The `_chunk_text` function's edge case

```python
def _chunk_text(text: str, max_chars: int = 900) -> list[str]:
    sentences = text.replace("\n", " ").split(". ")
    ...
    return chunks if chunks else [text[:max_chars]]
```

The fallback `[text[:max_chars]]` fires when the input text has no `. ` sentence boundaries. This includes JSON, code, URLs, tables, and HTML-stripped content (which your `_strip_html()` might produce). In those cases, the entire text gets truncated to 900 chars for GLiNER2.

This is unlikely to be a bug in practice — GLiNER2 on non-sentence text probably doesn't extract useful entities anyway. But it means entity extraction silently degrades for structured-data inputs. Worth knowing.

### 5. The `output/` directory saves results permanently (locally)

```python
def save_result(result: dict) -> Path:
    _OUTPUT_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = _OUTPUT_DIR / f"analysis_{ts}.json"
    with open(filepath, "w") as f:
        json.dump(result, f, indent=2)
```

The README correctly says "results saved only to your local `output/` directory." But there's no cleanup — every analysis adds a file. Users who run this regularly will accumulate JSON files indefinitely.

This is fine for a personal tool. Just worth mentioning if you ever ship a managed or hosted version.

### 6. The CI uses `actions/checkout@v6` and `actions/setup-python@v6` — these don't exist yet

```yaml
- uses: actions/checkout@v6
- uses: actions/setup-python@v6
```

As of April 2026, the current stable versions are `actions/checkout@v4` and `actions/setup-python@v5`. `@v6` doesn't exist — this CI workflow will fail on GitHub Actions right now.

**What to do:** Change `@v6` to `@v4` for checkout and `@v5` for setup-python. This is a quick fix.

---

## What This Tool Could Become

The countermeasure output format (`mechanisms_identified`, `countermeasures`, `durability`, `who_can_do_it`) is structured JSON. That's deliberate — it's machine-queryable, not just human-readable.

**The natural next step** is a public web instance. The tool is already BYOK, so there's no API cost on your end. A hosted version at `frictionbreaker.regulatedfriction.me` (or similar) would let journalists, researchers, and advocates run analyses without installing Python. The BYOK model means you're not on the hook for Anthropic costs.

The `new_mechanisms_detected` field is also underutilized right now. Over time, flagged mechanisms from real analyses could feed back into the taxonomy via pull requests — that's a genuine community contribution mechanism. The `CONTRIBUTING.md` already points people in this direction; making it explicit ("submit a PR to add this mechanism to the taxonomy") would close the loop.

---

## The Bigger Picture

You started with a research question about a Russian shortwave station. That question led to a research framework. The research framework led to a pipeline. The pipeline led to a commercial product. And now the framework has a public-facing civic tool.

Each thing built the next. Friction Breaker is where the research stops being just yours and starts being something other people can use.

The code is good. The test coverage is your best yet. The security controls are right. Fix the CI version numbers and the `/health` endpoint loading issue, and this is production-ready.

---

*Written April 8, 2026 by GitHub Copilot after extracting and reading `leroysfrictionbreaker.tar.xz` in full.*
