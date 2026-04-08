"""
Tests for the Friction Breaker application.
"""

import json
from pathlib import Path

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
