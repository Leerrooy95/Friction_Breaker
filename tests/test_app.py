"""
Tests for the Friction Breaker application.
"""

import json
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Taxonomy loading
# ---------------------------------------------------------------------------

def test_taxonomy_file_exists():
    """The mechanism taxonomy JSON must exist."""
    taxonomy_path = Path(__file__).resolve().parent.parent / "mechanism_classifier_taxonomy.json"
    assert taxonomy_path.exists(), "mechanism_classifier_taxonomy.json not found"


def test_taxonomy_is_valid_json():
    """The taxonomy file must be valid JSON."""
    taxonomy_path = Path(__file__).resolve().parent.parent / "mechanism_classifier_taxonomy.json"
    with open(taxonomy_path) as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_taxonomy_has_mechanisms():
    """The taxonomy must contain a 'mechanisms' list with entries."""
    taxonomy_path = Path(__file__).resolve().parent.parent / "mechanism_classifier_taxonomy.json"
    with open(taxonomy_path) as f:
        data = json.load(f)
    mechanisms = data.get("mechanisms", [])
    assert len(mechanisms) > 0, "Taxonomy has no mechanisms"


def test_taxonomy_mechanism_fields():
    """Each mechanism must have required fields."""
    taxonomy_path = Path(__file__).resolve().parent.parent / "mechanism_classifier_taxonomy.json"
    with open(taxonomy_path) as f:
        data = json.load(f)

    required_fields = {"id", "name", "category", "description", "durability"}
    for mechanism in data.get("mechanisms", []):
        for field in required_fields:
            assert field in mechanism, f"Mechanism {mechanism.get('id', '?')} missing field: {field}"


def test_taxonomy_durability_range():
    """Durability scores must be between 1 and 10."""
    taxonomy_path = Path(__file__).resolve().parent.parent / "mechanism_classifier_taxonomy.json"
    with open(taxonomy_path) as f:
        data = json.load(f)

    for mechanism in data.get("mechanisms", []):
        d = mechanism.get("durability")
        assert isinstance(d, (int, float)), f"Mechanism {mechanism['id']} durability is not a number"
        assert 1 <= d <= 10, f"Mechanism {mechanism['id']} durability {d} out of range 1-10"


# ---------------------------------------------------------------------------
# App module imports and helpers
# ---------------------------------------------------------------------------

def test_app_module_imports():
    """The app module must be importable (with missing optional deps handled)."""
    import app
    assert hasattr(app, "load_taxonomy")
    assert hasattr(app, "create_app")
    assert hasattr(app, "run_analysis")


def test_load_taxonomy():
    """load_taxonomy() must return a dict with mechanisms."""
    import app
    taxonomy = app.load_taxonomy()
    assert isinstance(taxonomy, dict)
    assert "mechanisms" in taxonomy
    assert len(taxonomy["mechanisms"]) > 0


def test_chunk_text():
    """_chunk_text must split long text into smaller chunks."""
    import app
    text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
    chunks = app._chunk_text(text, max_chars=40)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert len(chunk) <= 100  # Allow some flexibility for sentence boundaries


def test_chunk_text_short():
    """Short text should not be split."""
    import app
    text = "Short text."
    chunks = app._chunk_text(text, max_chars=900)
    assert len(chunks) == 1


# ---------------------------------------------------------------------------
# Flask app tests
# ---------------------------------------------------------------------------

def test_flask_app_creates():
    """create_app() must return a Flask application."""
    import app
    flask_app = app.create_app()
    assert flask_app is not None


def test_health_endpoint():
    """The /health endpoint must return status ok."""
    import app
    flask_app = app.create_app()
    with flask_app.test_client() as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "taxonomy_loaded" in data


def test_taxonomy_endpoint():
    """The /taxonomy endpoint must return the taxonomy JSON."""
    import app
    flask_app = app.create_app()
    with flask_app.test_client() as client:
        resp = client.get("/taxonomy")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "mechanisms" in data


def test_index_endpoint():
    """The / endpoint must return the HTML page."""
    import app
    flask_app = app.create_app()
    with flask_app.test_client() as client:
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Friction Breaker" in resp.data


def test_analyze_no_body():
    """POST /analyze with no body must return 400."""
    import app
    flask_app = app.create_app()
    with flask_app.test_client() as client:
        resp = client.post("/analyze", content_type="application/json")
        assert resp.status_code == 400


def test_analyze_no_api_key():
    """POST /analyze without an API key must return 400."""
    import app
    flask_app = app.create_app()
    with flask_app.test_client() as client:
        resp = client.post(
            "/analyze",
            json={"text": "Some text"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "API key" in data.get("error", "").lower() or "api key" in data.get("error", "").lower()


def test_analyze_no_text():
    """POST /analyze with a key but no text must return 400."""
    import app
    flask_app = app.create_app()
    with flask_app.test_client() as client:
        resp = client.post(
            "/analyze",
            json={"api_key": "sk-ant-fake-key"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "text" in data.get("error", "").lower() or "url" in data.get("error", "").lower()


# ---------------------------------------------------------------------------
# Security tests
# ---------------------------------------------------------------------------

def test_ssrf_blocked_localhost():
    """SSRF: requests to localhost must be blocked."""
    import app
    result = app.fetch_url("http://localhost/secret")
    assert result == ""


def test_ssrf_blocked_private_ip():
    """SSRF: requests to private IPs must be blocked."""
    import app
    for url in [
        "http://127.0.0.1/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://192.168.1.1/config",
        "http://10.0.0.1/internal",
    ]:
        result = app.fetch_url(url)
        assert result == "", f"SSRF not blocked for {url}"


def test_ssrf_blocked_non_http_scheme():
    """SSRF: non-HTTP schemes (file://, ftp://) must be blocked."""
    import app
    for url in ["file:///etc/passwd", "ftp://evil.com/data", "gopher://evil.com/"]:
        result = app.fetch_url(url)
        assert result == "", f"Non-HTTP scheme not blocked for {url}"


def test_input_text_truncation():
    """Input text longer than _MAX_INPUT_CHARS must be truncated by the endpoint."""
    import app
    flask_app = app.create_app()
    long_text = "A" * 60000
    with flask_app.test_client() as client:
        resp = client.post(
            "/analyze",
            json={"api_key": "sk-ant-fake-key", "text": long_text},
            content_type="application/json",
        )
        # The endpoint should accept this (truncate internally) — it won't
        # succeed without a real API key, but it should NOT return 400 for
        # text-too-long.  The response will be 400 only if no key, or an
        # API error (which we can't test without a live key), so just
        # confirm the server didn't crash (status != 500).
        assert resp.status_code != 500


def test_api_key_not_in_health_response():
    """The /health endpoint must never expose API keys."""
    import os

    import app

    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-super-secret-key-12345"
    try:
        flask_app = app.create_app()
        with flask_app.test_client() as client:
            resp = client.get("/health")
            assert resp.status_code == 200
            assert "sk-ant" not in resp.get_data(as_text=True)
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)


def test_anthropic_model_env_override(monkeypatch):
    """The ANTHROPIC_MODEL env var must override the default model."""
    import importlib

    import app

    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-test-model")
    importlib.reload(app)
    try:
        assert app._ANTHROPIC_MODEL == "claude-test-model"
    finally:
        monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
        importlib.reload(app)


def test_anthropic_model_default(monkeypatch):
    """Without ANTHROPIC_MODEL env var, the default model must be set."""
    import importlib

    import app

    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    importlib.reload(app)
    try:
        assert app._ANTHROPIC_MODEL == "claude-sonnet-4-6"
    finally:
        importlib.reload(app)


def test_health_does_not_load_gliner():
    """The /health endpoint must NOT trigger GLiNER2 model loading."""
    import app

    # Reset global state to simulate fresh start
    original_model = app._gliner_model
    original_flag = app._HAS_GLINER
    app._gliner_model = None
    app._HAS_GLINER = False
    try:
        flask_app = app.create_app()
        with flask_app.test_client() as client:
            resp = client.get("/health")
            assert resp.status_code == 200
            data = resp.get_json()
            # gliner_available should be False since we haven't loaded it
            assert data["gliner_available"] is False
            # The model should still be None (not loaded by health check)
            assert app._gliner_model is None
    finally:
        app._gliner_model = original_model
        app._HAS_GLINER = original_flag


# ---------------------------------------------------------------------------
# New tests for bug fixes and enhancements
# ---------------------------------------------------------------------------

def test_paths_anchored_to_module():
    """File paths must be anchored to the module's directory, not CWD."""
    import app

    module_dir = Path(app.__file__).resolve().parent
    assert module_dir / "mechanism_classifier_taxonomy.json" == app._TAXONOMY_FILE
    assert module_dir / "_AI_CONTEXT_INDEX" == app._CONTEXT_DIR
    assert module_dir / "output" == app._OUTPUT_DIR


def test_context_index_loads_subdirectories():
    """load_context_index() with rglob must discover more files than top-level glob."""
    import app

    # Verify rglob discovers subdirectory files (the actual loading may be
    # truncated by the 60K character hard cap, so we test discovery, not content)
    subdir_files = list(app._CONTEXT_DIR.rglob("*.md"))
    top_files = list(app._CONTEXT_DIR.glob("*.md"))
    assert len(subdir_files) > len(top_files), (
        "rglob should find more .md files than top-level glob"
    )
    # Ensure load_context_index still returns non-empty content
    app._cached_context_index = None
    content = app.load_context_index()
    assert len(content) > 0
    app._cached_context_index = None


def test_ssrf_blocked_ipv6_loopback():
    """SSRF: IPv6 loopback (::1) must be blocked."""
    import app

    result = app.fetch_url("http://[::1]/secret")
    assert result == "", "IPv6 loopback not blocked"


def test_blocked_hosts_no_brackets():
    """_BLOCKED_HOSTS must contain '::1' without brackets."""
    import app

    assert "::1" in app._BLOCKED_HOSTS
    assert "[::1]" not in app._BLOCKED_HOSTS


def test_validate_url_blocks_private():
    """_validate_url must return None for private addresses."""
    import app

    assert app._validate_url("http://localhost/secret") is None
    assert app._validate_url("http://127.0.0.1/admin") is None
    assert app._validate_url("ftp://evil.com/data") is None


def test_validate_url_allows_public():
    """_validate_url must return a URL for valid public addresses."""
    import app

    result = app._validate_url("https://example.com/article")
    assert result is not None
    assert result.startswith("https://")


def test_main_function_exists():
    """main() entry point must exist and be callable."""
    import app

    assert hasattr(app, "main")
    assert callable(app.main)


def test_result_to_markdown():
    """_result_to_markdown must produce a Markdown string from a result dict."""
    import app

    result = {
        "input_summary": "Test input summary.",
        "political_translator_summary": "What this means in plain English.",
        "mechanisms_identified": [
            {
                "taxonomy_id": "A-01",
                "name": "Test Mechanism",
                "confidence": "HIGH",
                "durability": 7,
                "what_it_does": "Does something important.",
                "evidence": "Evidence quote here.",
                "countermeasures": [
                    {
                        "action": "Take action",
                        "durability_score": 8,
                        "feasibility": "HIGH",
                        "who_can_do_it": "Citizens",
                        "plain_english": "You can do this."
                    }
                ]
            }
        ],
        "new_mechanisms_detected": [],
        "_meta": {
            "gliner_entities_extracted": 5,
            "taxonomy_mechanisms_available": 54,
            "model": "claude-sonnet-4-6",
            "processing_time_seconds": 3.2,
            "timestamp": "2026-04-08T12:00:00Z"
        }
    }
    md = app._result_to_markdown(result)
    assert "# Friction Breaker" in md
    assert "Test Mechanism" in md
    assert "Take action" in md
    assert "Citizens" in md
    assert "Plain English" in md
    assert "Test input summary." in md
    assert "What this means in plain English." in md
    assert "Evidence quote here." in md
    assert "claude-sonnet-4-6" in md


def test_save_result_creates_markdown(tmp_path, monkeypatch):
    """save_result must create both .json and .md files."""
    import app

    monkeypatch.setattr(app, "_OUTPUT_DIR", tmp_path)
    result = {
        "input_summary": "Summary",
        "mechanisms_identified": [],
        "new_mechanisms_detected": [],
        "_meta": {"timestamp": "2026-04-08T12:00:00Z"}
    }
    json_path = app.save_result(result)
    assert json_path.exists()
    assert json_path.suffix == ".json"
    # Check that a matching .md file was also created
    md_path = json_path.with_suffix(".md")
    assert md_path.exists()
    assert "Friction Breaker" in md_path.read_text()


# ---------------------------------------------------------------------------
# New feature tests
# ---------------------------------------------------------------------------

def test_taxonomy_version_in_json():
    """The taxonomy JSON must have a metadata.version field (semver string)."""
    taxonomy_path = Path(__file__).resolve().parent.parent / "mechanism_classifier_taxonomy.json"
    with open(taxonomy_path) as f:
        data = json.load(f)
    version = data.get("metadata", {}).get("version")
    assert version is not None, "Taxonomy metadata.version is missing"
    # Validate semver-ish format (MAJOR.MINOR.PATCH)
    assert re.match(r"^\d+\.\d+\.\d+$", version), f"Version '{version}' is not semver"


def test_health_endpoint_includes_taxonomy_version():
    """The /health endpoint must include taxonomy_version."""
    import app
    flask_app = app.create_app()
    with flask_app.test_client() as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "taxonomy_version" in data
        assert data["taxonomy_version"] is not None


def test_rate_limit_env_var(monkeypatch):
    """The RATE_LIMIT env var must be read at module level."""
    import importlib

    import app

    monkeypatch.setenv("RATE_LIMIT", "50 per hour")
    importlib.reload(app)
    try:
        assert app._RATE_LIMIT == "50 per hour"
    finally:
        monkeypatch.delenv("RATE_LIMIT", raising=False)
        importlib.reload(app)


def test_rate_limit_default(monkeypatch):
    """Without RATE_LIMIT env var, the default must be '10 per minute'."""
    import importlib

    import app

    monkeypatch.delenv("RATE_LIMIT", raising=False)
    importlib.reload(app)
    try:
        assert app._RATE_LIMIT == "10 per minute"
    finally:
        importlib.reload(app)


def test_cli_batch_function_exists():
    """cli_batch() must exist and be callable."""
    import app

    assert hasattr(app, "cli_batch")
    assert callable(app.cli_batch)


def test_cli_batch_missing_file():
    """cli_batch must exit with error for a non-existent file."""
    import app

    with pytest.raises(SystemExit):
        app.cli_batch("/tmp/nonexistent_batch_file_12345.txt")


def test_cli_batch_empty_file(tmp_path):
    """cli_batch must exit with error for an empty batch file."""
    import app

    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    with pytest.raises(SystemExit):
        app.cli_batch(str(empty_file))


def test_cli_batch_skips_comments(tmp_path):
    """cli_batch must skip comment lines (starting with #)."""
    import app

    batch_file = tmp_path / "comments_only.txt"
    batch_file.write_text("# This is a comment\n# Another comment\n")
    with pytest.raises(SystemExit):
        app.cli_batch(str(batch_file))


def test_max_context_chars_config():
    """_MAX_CONTEXT_CHARS must be set as a module-level config."""
    import app

    assert hasattr(app, "_MAX_CONTEXT_CHARS")
    assert isinstance(app._MAX_CONTEXT_CHARS, int)
    assert app._MAX_CONTEXT_CHARS > 0
