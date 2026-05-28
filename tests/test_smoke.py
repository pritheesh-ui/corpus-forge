import os
import tempfile
from pathlib import Path

_tmpdir = tempfile.mkdtemp(prefix="docchat-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/app.db"
os.environ["UPLOAD_DIR"] = _tmpdir

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.services import retriever


SAMPLE_MD = b"""# BM25 Retrieval

BM25 is a ranking function used by search engines. Unlike TF-IDF, BM25 saturates term frequency.

## Parameters

The k1 parameter controls term frequency saturation. The b parameter controls length normalization.
Typical values: k1 around 1.5, b around 0.75.
"""

SAMPLE_PY = b"""def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("cannot divide by zero")
    return a / b


def add(a, b):
    return a + b
"""


def test_upload_and_retrieve():
    client = TestClient(app)

    response = client.post(
        "/files/upload",
        files=[
            ("files", ("notes.md", SAMPLE_MD, "text/markdown")),
            ("files", ("math.py", SAMPLE_PY, "text/x-python")),
        ],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["saved"] == 2
    assert payload["skipped"] == []

    db = SessionLocal()
    try:
        results = retriever.retrieve(db, "length normalization b parameter", None, 5)
        assert results, "expected results from BM25"
        top = results[0]
        assert top.document_name == "notes.md"

        code_results = retriever.retrieve(db, "divide function zero", None, 5)
        assert any(r.document_name == "math.py" for r in code_results)
    finally:
        db.close()


def test_unsupported_extension_rejected():
    client = TestClient(app)
    response = client.post(
        "/files/upload",
        files=[("files", ("bad.exe", b"MZ stub", "application/octet-stream"))],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["saved"] == 0
    assert any("bad.exe" in s for s in payload["skipped"])


def test_chat_create_and_settings():
    client = TestClient(app)

    create = client.post("/chats/new", json={"mode": "quiz", "options": {"count": 5}})
    assert create.status_code == 200
    chat_id = create.json()["id"]

    update = client.post(
        f"/chats/{chat_id}/settings",
        json={"mode": "code_review", "options": {"focus": "performance", "level": "advanced", "tone": "concise"}},
    )
    assert update.status_code == 200

    page = client.get(f"/chat/{chat_id}")
    assert page.status_code == 200
    assert "code_review" in page.text or "code review" in page.text


def test_send_message_without_api_key_returns_503():
    client = TestClient(app)
    create = client.post("/chats/new", json={"mode": "ask", "options": {}})
    chat_id = create.json()["id"]

    response = client.post(
        f"/chats/{chat_id}/messages",
        json={"content": "hello?", "document_ids": []},
    )
    assert response.status_code == 503
    assert "GOOGLE_API_KEY" in response.text


if __name__ == "__main__":
    test_upload_and_retrieve()
    test_unsupported_extension_rejected()
    test_chat_create_and_settings()
    test_send_message_without_api_key_returns_503()
    print("all tests passed")
