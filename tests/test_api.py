from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.database import get_db

client = TestClient(app)

# Test 1: Check the home endpoint
def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"

# Test 2: Check the health endpoint
def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

# Test 3: Check verification when no relevant evidence is found
def test_verify_with_insufficient_evidence():
    mock_db = MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with patch(
            "app.main.fetch_live_news_evidence",
            return_value=[]
        ), patch(
            "app.main.filter_relevant_evidence",
            return_value=[]
        ), patch(
            "app.main.save_verification_result"
        ) as mock_save:

            saved_claim = MagicMock()
            saved_claim.id = 100
            mock_save.return_value = saved_claim

            response = client.post(
                "/verify",
                json={
                    "claim": (
                        "A newly discovered planet named Xylora "
                        "will be announced tomorrow."
                    )
                }
            )

            assert response.status_code == 200

            data = response.json()

            assert data["claim_id"] == 100
            assert data["verdict"] == "UNVERIFIED"
            assert data["confidence_score"] == 0
            assert data["evidence_count"] == 0
            assert data["sources"] == []

    finally:
        app.dependency_overrides.clear()

# Test 4: Check validation for claims shorter than 5 characters
def test_verify_rejects_short_claim():
    response = client.post(
        "/verify",
        json={"claim": "Hi"}
    )

    assert response.status_code == 422

# Test 5: Check the verification history endpoint
def test_history_endpoint():
    mock_db = MagicMock()

    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/history")

        assert response.status_code == 200
        assert response.json() == []

    finally:
        app.dependency_overrides.clear()

# Test 6: Check verification when relevant evidence is found
def test_verify_with_relevant_evidence():
    mock_db = MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_db

    article = {
        "title": "Chandrayaan-3 Successfully Lands on Moon",
        "url": "https://example.com/chandrayaan",
        "content": "Chandrayaan-3 successfully landed on the Moon."
    }

    evidence = {
        "evidence_sentence": (
            "Chandrayaan-3 successfully landed on the Moon."
        ),
        "source_title": "Chandrayaan-3 Successfully Lands on Moon",
        "source_url": "https://example.com/chandrayaan",
        "similarity_score": 0.95
    }

    report = {
        "verdict": "SUPPORTED",
        "confidence_score": 95,
        "explanation": "The evidence supports the claim.",
        "past_events": [],
        "current_status": "Chandrayaan-3 landed successfully.",
        "future_outlook": [],
        "sources": [
            {
                "title": "Chandrayaan-3 Successfully Lands on Moon",
                "url": "https://example.com/chandrayaan"
            }
        ]
    }

    try:
        with patch(
            "app.main.fetch_live_news_evidence",
            return_value=[article]
        ), patch(
            "app.main.filter_relevant_evidence",
            return_value=[evidence]
        ), patch(
            "app.main.analyze_claim_with_llm",
            return_value=report
        ), patch(
            "app.main.save_verification_result"
        ) as mock_save:

            saved_claim = MagicMock()
            saved_claim.id = 101
            mock_save.return_value = saved_claim

            response = client.post(
                "/verify",
                json={
                    "claim": "Chandrayaan-3 successfully landed on the Moon."
                }
            )

            assert response.status_code == 200

            data = response.json()

            assert data["claim_id"] == 101
            assert data["verdict"] == "SUPPORTED"
            assert data["confidence_score"] == 95
            assert data["evidence_count"] == 1
            assert len(data["sources"]) == 1

            mock_save.assert_called_once()

    finally:
        app.dependency_overrides.clear()

def test_verify_returns_source_metadata():
    mock_db = MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_db

    evidence = [
        {
            "evidence_sentence": (
                "Chandrayaan-3 successfully landed on the Moon."
            ),
            "source_title": "ISRO Mission Update",
            "source_url": "https://www.isro.gov.in/news",
            "source_domain": "isro.gov.in",
            "source_category": "official",
            "similarity_score": 0.95
        }
    ]

    report = {
        "verdict": "SUPPORTED",
        "confidence_score": 95,
        "explanation": "The retrieved evidence supports the claim.",
        "past_events": [],
        "current_and_future_updates": [],
        "sources": [
            {
                "title": "ISRO Mission Update",
                "url": "https://www.isro.gov.in/news",
                "domain": "isro.gov.in",
                "source_category": "official"
            }
        ]
    }

    try:
        with patch(
            "app.main.fetch_live_news_evidence",
            return_value=[{"title": "ISRO Mission Update"}]
        ), patch(
            "app.main.filter_relevant_evidence",
            return_value=evidence
        ), patch(
            "app.main.analyze_claim_with_llm",
            return_value=report
        ), patch(
            "app.main.save_verification_result"
        ) as mock_save:

            saved_claim = MagicMock()
            saved_claim.id = 102
            mock_save.return_value = saved_claim

            response = client.post(
                "/verify",
                json={
                    "claim": (
                        "Chandrayaan-3 successfully landed on the Moon."
                    )
                }
            )

            assert response.status_code == 200

            data = response.json()

            assert data["claim_id"] == 102
            assert data["verdict"] == "SUPPORTED"
            assert data["evidence_count"] == 1

            assert data["sources"][0]["domain"] == "isro.gov.in"
            assert data["sources"][0]["source_category"] == "official"

            assert data["evidence"][0]["source_domain"] == "isro.gov.in"
            assert data["evidence"][0]["source_category"] == "official"

            assert data["evidence_status"] == "EVIDENCE_FOUND"

            mock_save.assert_called_once()

    finally:
        app.dependency_overrides.clear()
