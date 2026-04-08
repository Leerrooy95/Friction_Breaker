"""
app.py — Friction Breaker: Mechanism Classifier + Countermeasure Engine
========================================================================
BYOK Flask application that takes user-provided text (news articles,
executive orders, legislative text, regulatory actions), extracts
entities via GLiNER2 (local, zero-cost), classifies mechanisms against
the taxonomy, and generates countermeasure analysis via Anthropic Claude.

Usage:
    python app.py                          # Start Flask server (port 5000)
    python app.py --port 8080              # Custom port
    python app.py --analyze "text here"    # CLI mode, skip Flask

Requires: ANTHROPIC_API_KEY in .env or environment.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ─── Dependency checks ────────────────────────────────────────────────────────
try:
    from flask import Flask, jsonify, render_template, request
    _HAS_FLASK = True
except ImportError:
    _HAS_FLASK = False
    logger.warning("Flask not installed. CLI mode only. Run: pip install flask")

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    _HAS_LIMITER = True
except ImportError:
    _HAS_LIMITER = False

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False
    logger.error("anthropic package not installed. Run: pip install anthropic")

try:
    import requests as req_lib
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
    logger.warning("requests not installed. URL fetching disabled.")

# ─── GLiNER2 (local, zero-cost entity extraction) ────────────────────────────
_HAS_GLINER = False
_gliner_model = None

def _load_gliner():
    """Lazy-load GLiNER2 model (first call only)."""
    global _HAS_GLINER, _gliner_model
    if _gliner_model is not None:
        return _gliner_model
    try:
        from gliner import GLiNER
        logger.info("Loading GLiNER model (first run downloads ~400MB)...")
        _gliner_model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
        _HAS_GLINER = True
        logger.info("GLiNER model loaded.")
        return _gliner_model
    except ImportError:
        logger.warning("GLiNER not installed. Entity extraction will use Claude only.")
        return None
    except Exception as e:
        logger.warning(f"GLiNER load failed: {e}. Entity extraction will use Claude only.")
        return None


# ─── CONFIG ───────────────────────────────────────────────────────────────────
_ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
_MAX_INPUT_CHARS = 50000
_BASE_DIR = Path(__file__).resolve().parent
_TAXONOMY_FILE = _BASE_DIR / "mechanism_classifier_taxonomy.json"
_CONTEXT_DIR = _BASE_DIR / "_AI_CONTEXT_INDEX"
_OUTPUT_DIR = _BASE_DIR / "output"

# ─── Cached data (loaded once, reused across requests) ───────────────────────
_cached_taxonomy: dict | None = None
_cached_context_index: str | None = None

# Entity labels for GLiNER2 — tuned for mechanism detection
_GLINER_LABELS = [
    "legislation", "law", "act", "bill", "statute", "regulation",
    "executive order", "policy", "rule", "amendment",
    "person", "politician", "official", "judge",
    "organization", "agency", "department", "committee", "fund",
    "company", "corporation", "shell company",
    "jurisdiction", "state", "country",
    "court case", "lawsuit", "ruling", "injunction",
    "financial instrument", "stablecoin", "cryptocurrency",
    "mechanism", "procedure", "exemption", "designation",
    "tax incentive", "abatement", "rider", "charter",
]

# ─── Load taxonomy ────────────────────────────────────────────────────────────
def load_taxonomy() -> dict:
    """Load the mechanism classifier taxonomy (cached after first call)."""
    global _cached_taxonomy
    if _cached_taxonomy is not None:
        return _cached_taxonomy
    if not _TAXONOMY_FILE.exists():
        logger.error(f"Taxonomy file not found: {_TAXONOMY_FILE}")
        return {"mechanisms": [], "categories": []}
    with open(_TAXONOMY_FILE) as f:
        _cached_taxonomy = json.load(f)
    return _cached_taxonomy


def load_context_index() -> str:
    """Load all markdown files from _AI_CONTEXT_INDEX into a single string (cached after first call)."""
    global _cached_context_index
    if _cached_context_index is not None:
        return _cached_context_index
    if not _CONTEXT_DIR.exists():
        return ""
    parts = []
    for md_file in sorted(_CONTEXT_DIR.rglob("*.md")):
        try:
            content = md_file.read_text(errors="replace")
            # Truncate individual files to keep total context manageable
            if len(content) > 8000:
                content = content[:8000] + "\n\n[... truncated for context window ...]"
            parts.append(f"## {md_file.name}\n\n{content}")
        except Exception as e:
            logger.warning(f"Could not read {md_file}: {e}")
    combined = "\n\n---\n\n".join(parts)
    # Hard cap on total context
    if len(combined) > 60000:
        combined = combined[:60000] + "\n\n[... truncated ...]"
    _cached_context_index = combined
    return _cached_context_index


# ─── GLiNER2 entity extraction ────────────────────────────────────────────────
def extract_entities_gliner(text: str) -> list[dict]:
    """Extract entities from text using GLiNER2 (local, zero-cost)."""
    model = _load_gliner()
    if model is None:
        return []

    # GLiNER works best on chunks < 1000 chars
    chunks = _chunk_text(text, max_chars=900)
    all_entities = []
    seen = set()

    for chunk in chunks:
        try:
            entities = model.predict_entities(chunk, _GLINER_LABELS, threshold=0.4)
            for ent in entities:
                key = (ent["text"].lower().strip(), ent["label"])
                if key not in seen:
                    seen.add(key)
                    all_entities.append({
                        "text": ent["text"].strip(),
                        "label": ent["label"],
                        "score": round(ent["score"], 3)
                    })
        except Exception as e:
            logger.warning(f"GLiNER extraction error on chunk: {e}")

    # Sort by confidence
    all_entities.sort(key=lambda x: x["score"], reverse=True)
    return all_entities


def _chunk_text(text: str, max_chars: int = 900) -> list[str]:
    """Split text into chunks at sentence boundaries."""
    sentences = text.replace("\n", " ").split(". ")
    chunks = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) + 2 > max_chars:
            if current:
                chunks.append(current.strip())
            current = sent + ". "
        else:
            current += sent + ". "
    if current.strip():
        chunks.append(current.strip())
    return chunks if chunks else [text[:max_chars]]


# ─── Claude API: Mechanism Classification + Countermeasure Analysis ──────────
def analyze_with_claude(
    text: str,
    entities: list[dict],
    taxonomy: dict,
    context_index: str,
    api_key: str
) -> dict:
    """
    Send text + extracted entities + taxonomy to Claude for:
    1. Mechanism classification (which taxonomy entries match)
    2. Countermeasure analysis (ranked by durability)
    3. Plain-English explanation (Political Translator format)
    """
    if not _HAS_ANTHROPIC:
        return {"error": "anthropic package not installed"}

    client = anthropic.Anthropic(api_key=api_key)

    # Build taxonomy summary for the prompt
    taxonomy_summary = json.dumps([
        {
            "id": m["id"],
            "name": m["name"],
            "category": m["category"],
            "description": m["description"],
            "durability": m["durability"],
            "reversal_pathways": m["reversal_pathways"]
        }
        for m in taxonomy.get("mechanisms", [])
    ], indent=1)

    entity_summary = json.dumps(entities[:30], indent=1) if entities else "No entities extracted."

    # Truncate input text for prompt
    input_text = text[:12000] if len(text) > 12000 else text

    prompt = f"""You are the Friction Breaker — a countermeasure analysis engine.

You have two knowledge sources:
1. A MECHANISM CLASSIFIER TAXONOMY — a structured database of every legal, regulatory, personnel, financial, and procedural mechanism documented in The Regulated Friction Project.
2. A BACKGROUND KNOWLEDGE BASE — research context from the _AI_CONTEXT_INDEX.

Your job:
1. Read the user's input text.
2. Identify which mechanisms from the taxonomy are being deployed, referenced, or enabled.
3. For each identified mechanism, retrieve its reversal pathways.
4. Generate a COUNTERMEASURE REPORT in plain English that anyone can understand.

## MECHANISM TAXONOMY
{taxonomy_summary}

## EXTRACTED ENTITIES (from GLiNER2, local extraction)
{entity_summary}

## USER INPUT TEXT
{input_text}

## OUTPUT FORMAT

Respond with a JSON object containing:
{{
  "timestamp": "ISO 8601",
  "input_summary": "2-3 sentence summary of what the user submitted",
  "mechanisms_identified": [
    {{
      "taxonomy_id": "A-01",
      "name": "Mechanism name from taxonomy",
      "confidence": "HIGH / MEDIUM / LOW",
      "evidence": "Quote or reference from the input text that triggered this match",
      "what_it_does": "1-2 sentence plain-English explanation of what this mechanism does to citizens",
      "durability": 6,
      "countermeasures": [
        {{
          "action": "Specific countermeasure from reversal_pathways",
          "durability_score": 7,
          "feasibility": "HIGH / MEDIUM / LOW",
          "who_can_do_it": "Who has the power to implement this (citizens, state legislature, Congress, courts, etc.)",
          "plain_english": "What this means in everyday language"
        }}
      ]
    }}
  ],
  "new_mechanisms_detected": [
    {{
      "name": "If you identify a mechanism NOT in the taxonomy",
      "description": "What it does",
      "suggested_category": "A-H",
      "suggested_durability": 5,
      "why_it_matters": "Plain English"
    }}
  ],
  "political_translator_summary": "A 3-5 paragraph summary written at an 8th-grade reading level explaining what was found, what it means for ordinary people, and what can be done about it. Use the same style as the DAILY_REPORTS Political Translator: short sentences, define technical terms inline, be specific about costs and impacts."
}}

IMPORTANT:
- Respond ONLY with the JSON object. No markdown fences. No preamble.
- Every countermeasure must specify WHO can implement it.
- Rank countermeasures by durability (hardest to remove first).
- If no mechanisms match, say so honestly — don't force matches.
- If you detect a mechanism NOT in the taxonomy, add it to new_mechanisms_detected.
"""

    try:
        response = client.messages.create(
            model=_ANTHROPIC_MODEL,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()

        # Clean potential markdown fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

        result = json.loads(raw)
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Claude returned invalid JSON: {e}")
        return {"error": "Claude returned an invalid response. Please try again."}
    except anthropic.AuthenticationError:
        return {"error": "Invalid API key. Check your ANTHROPIC_API_KEY."}
    except anthropic.RateLimitError:
        return {"error": "Rate limited. Wait a moment and try again."}
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return {"error": "An error occurred during analysis. Please try again."}


# ─── URL fetching ─────────────────────────────────────────────────────────────
_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal", "169.254.169.254"}

_RE_WHITESPACE = re.compile(r"\s+")


def _is_private_host(hostname: str) -> bool:
    """Check if a hostname resolves to a private/internal address."""
    import ipaddress
    import socket

    if hostname in _BLOCKED_HOSTS:
        return True
    if hostname.endswith(".local"):
        return True
    # Block common private IP ranges by prefix
    for prefix in ("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.",
                    "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
                    "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31."):
        if hostname.startswith(prefix):
            return True
    # Resolve DNS and check if the IP is private
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for _family, _type, _proto, _canonname, sockaddr in addr_info:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
    except (socket.gaierror, ValueError):
        pass
    return False


def _strip_html(text: str) -> str:
    """Remove HTML tags and normalize whitespace using the standard library parser."""
    from html.parser import HTMLParser

    class _TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self._pieces: list[str] = []
            self._skip = False

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self._skip = True

        def handle_endtag(self, tag):
            if tag in ("script", "style"):
                self._skip = False

        def handle_data(self, data):
            if not self._skip:
                self._pieces.append(data)

    parser = _TextExtractor()
    parser.feed(text)
    combined = " ".join(parser._pieces)
    return _RE_WHITESPACE.sub(" ", combined).strip()


_MAX_REDIRECTS = 5


def _validate_url(url: str) -> str | None:
    """Validate a URL's scheme and hostname. Returns the safe URL or None."""
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if _is_private_host(hostname):
        logger.warning("Blocked request to private/internal address")
        return None
    if parsed.scheme not in ("http", "https"):
        logger.warning("Blocked request with non-HTTP scheme")
        return None
    safe_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if parsed.query:
        safe_url += f"?{parsed.query}"
    return safe_url


def fetch_url(url: str) -> str:
    """Fetch text content from a URL. Blocks private/internal addresses.

    Follows redirects (up to ``_MAX_REDIRECTS`` hops) while re-validating
    each intermediate destination against the SSRF blocklist.
    """
    if not _HAS_REQUESTS:
        return ""
    try:
        current_url = url
        for _hop in range(_MAX_REDIRECTS + 1):
            safe_url = _validate_url(current_url)
            if safe_url is None:
                return ""

            resp = req_lib.get(safe_url, timeout=15, allow_redirects=False, headers={
                "User-Agent": "FrictionBreaker/1.0 (OSINT research tool)"
            })

            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("Location", "")
                if not location:
                    logger.warning("Redirect with no Location header")
                    return ""
                current_url = location
                continue

            resp.raise_for_status()
            text = _strip_html(resp.text)
            return text[:_MAX_INPUT_CHARS]

        logger.warning("Too many redirects")
        return ""
    except Exception as e:
        logger.warning(f"URL fetch failed: {e}")
        return ""


# ─── Save results ─────────────────────────────────────────────────────────────
def save_result(result: dict) -> Path:
    """Save analysis result to output/ directory as JSON and Markdown."""
    _OUTPUT_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Save JSON
    json_path = _OUTPUT_DIR / f"analysis_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    logger.info(f"Result saved: {json_path}")

    # Save Markdown report
    md_path = _OUTPUT_DIR / f"analysis_{ts}.md"
    md_path.write_text(_result_to_markdown(result))
    logger.info(f"Markdown report saved: {md_path}")

    return json_path


def _result_to_markdown(result: dict) -> str:
    """Convert an analysis result dict to a human-readable Markdown report."""
    lines: list[str] = []
    meta = result.get("_meta", {})
    ts = meta.get("timestamp", datetime.now(timezone.utc).isoformat())
    lines.append("# Friction Breaker — Countermeasure Report\n")
    lines.append(f"*Generated {ts}*\n")

    # Input summary
    if result.get("input_summary"):
        lines.append("## Input Summary\n")
        lines.append(f"{result['input_summary']}\n")

    # Plain-English summary
    if result.get("political_translator_summary"):
        lines.append("## What This Means (Plain English)\n")
        lines.append(f"{result['political_translator_summary']}\n")

    # Mechanisms identified
    mechanisms = result.get("mechanisms_identified", [])
    if mechanisms:
        lines.append("## Mechanisms Identified\n")
        for m in mechanisms:
            conf = m.get("confidence", "?")
            dur = m.get("durability", "?")
            lines.append(f"### {m.get('taxonomy_id', '?')} — {m.get('name', 'Unknown')}\n")
            lines.append(f"**Confidence:** {conf} · **Durability:** {dur}/10\n")
            if m.get("what_it_does"):
                lines.append(f"{m['what_it_does']}\n")
            if m.get("evidence"):
                lines.append(f"> *Evidence:* {m['evidence']}\n")
            cms = m.get("countermeasures", [])
            if cms:
                lines.append("#### Countermeasures\n")
                for c in cms:
                    lines.append(
                        f"- **{c.get('action', '')}** "
                        f"(durability {c.get('durability_score', '?')}/10, "
                        f"feasibility {c.get('feasibility', '?')})\n"
                        f"  - *Who can do it:* {c.get('who_can_do_it', '?')}\n"
                        f"  - {c.get('plain_english', '')}\n"
                    )

    # New mechanisms
    new_mechs = result.get("new_mechanisms_detected", [])
    if new_mechs:
        lines.append("## New Mechanisms Detected (Not in Taxonomy)\n")
        for nm in new_mechs:
            lines.append(
                f"- **{nm.get('name', '')}** "
                f"(category {nm.get('suggested_category', '?')}, "
                f"durability {nm.get('suggested_durability', '?')}/10)\n"
                f"  - {nm.get('description', '')}\n"
                f"  - *Why it matters:* {nm.get('why_it_matters', '')}\n"
            )

    # Metadata footer
    if meta:
        lines.append("---\n")
        lines.append(
            f"*Entities extracted: {meta.get('gliner_entities_extracted', 0)} · "
            f"Taxonomy: {meta.get('taxonomy_mechanisms_available', 0)} mechanisms · "
            f"Model: {meta.get('model', '?')} · "
            f"Processing time: {meta.get('processing_time_seconds', '?')}s*\n"
        )

    return "\n".join(lines)


# ─── Full analysis pipeline ───────────────────────────────────────────────────
def run_analysis(text: str, api_key: str) -> dict:
    """Run the full Friction Breaker pipeline on input text."""
    start = time.time()

    # 1. Load taxonomy
    taxonomy = load_taxonomy()
    if not taxonomy.get("mechanisms"):
        return {"error": "Taxonomy not loaded. Ensure mechanism_classifier_taxonomy.json exists."}

    # 2. Load context index
    context_index = load_context_index()

    # 3. Extract entities (GLiNER2, local, zero-cost)
    logger.info("Extracting entities with GLiNER2...")
    entities = extract_entities_gliner(text)
    logger.info(f"Extracted {len(entities)} entities.")

    # 4. Classify and analyze (Claude API)
    logger.info("Sending to Claude for mechanism classification + countermeasure analysis...")
    result = analyze_with_claude(text, entities, taxonomy, context_index, api_key)

    # 5. Add metadata
    result["_meta"] = {
        "gliner_entities_extracted": len(entities),
        "gliner_entities": entities[:20],
        "taxonomy_mechanisms_available": len(taxonomy.get("mechanisms", [])),
        "context_index_loaded": bool(context_index),
        "processing_time_seconds": round(time.time() - start, 2),
        "model": _ANTHROPIC_MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # 6. Save
    save_result(result)

    return result


# ─── Flask App ────────────────────────────────────────────────────────────────
def create_app():
    app = Flask(__name__)

    # Rate limiting — protects against quota exhaustion on /analyze
    if _HAS_LIMITER:
        limiter = Limiter(
            get_remote_address,
            app=app,
            default_limits=[],
            storage_uri="memory://",
        )

        @app.errorhandler(429)
        def rate_limit_handler(e):
            return jsonify({"error": "Rate limit exceeded. Please wait before trying again."}), 429
    else:
        limiter = None

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/analyze", methods=["POST"])
    def analyze():  # Rate-limited to 10/min per IP when flask-limiter is available (applied below)
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body"}), 400

        api_key = data.get("api_key", "").strip()
        text = data.get("text", "").strip()
        url = data.get("url", "").strip()

        if not api_key:
            # Fall back to env var
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            return jsonify({"error": "No API key provided. Set ANTHROPIC_API_KEY or enter it in the form."}), 400

        # Get text from URL if provided
        if url and not text:
            text = fetch_url(url)
            if not text:
                return jsonify({"error": "Could not fetch content from the provided URL."}), 400

        if not text:
            return jsonify({"error": "No text provided. Paste text or provide a URL."}), 400

        if len(text) > _MAX_INPUT_CHARS:
            text = text[:_MAX_INPUT_CHARS]

        result = run_analysis(text, api_key)
        return jsonify(result)

    # Apply rate limit to /analyze only (avoids interfering with health/taxonomy/index)
    if limiter is not None:
        analyze = limiter.limit("10 per minute")(analyze)

    @app.route("/taxonomy")
    def taxonomy_view():
        taxonomy = load_taxonomy()
        return jsonify(taxonomy)

    @app.route("/health")
    def health():
        return jsonify({
            "status": "ok",
            "gliner_available": _HAS_GLINER,
            "anthropic_available": _HAS_ANTHROPIC,
            "taxonomy_loaded": _TAXONOMY_FILE.exists(),
            "context_index_loaded": _CONTEXT_DIR.exists()
        })

    return app


# ─── CLI Mode ─────────────────────────────────────────────────────────────────
def cli_analyze(text: str):
    """Run analysis from command line."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)
    result = run_analysis(text, api_key)
    print(json.dumps(result, indent=2))


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    """Entry point for both ``python app.py`` and the ``friction-breaker`` console script."""
    parser = argparse.ArgumentParser(description="Friction Breaker — Countermeasure Engine")
    parser.add_argument("--port", type=int, default=5000, help="Flask server port")
    parser.add_argument("--analyze", type=str, help="Analyze text directly (CLI mode)")
    parser.add_argument("--url", type=str, help="Fetch and analyze a URL (CLI mode)")
    args = parser.parse_args()

    if args.analyze:
        cli_analyze(args.analyze)
    elif args.url:
        text = fetch_url(args.url)
        if text:
            cli_analyze(text)
        else:
            logger.error(f"Could not fetch URL: {args.url}")
    else:
        if not _HAS_FLASK:
            logger.error("Flask not installed. Install it: pip install flask")
            sys.exit(1)
        app = create_app()
        print(f"\n🔧 Friction Breaker running on http://localhost:{args.port}")
        print(f"   Taxonomy: {len(load_taxonomy().get('mechanisms', []))} mechanisms loaded")
        print(f"   GLiNER2: {'available' if _load_gliner() else 'not available (Claude-only mode)'}")
        print("   BYOK: Enter your ANTHROPIC_API_KEY in the web interface\n")
        app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
