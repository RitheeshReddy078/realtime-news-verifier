
from unittest.mock import patch, MagicMock

from app.search import (
    normalize_url,
    get_source_metadata,
    fetch_live_news_evidence,
    generate_verification_queries,
    fetch_claim_evidence
)


def test_normalize_url():
    result = normalize_url(
        "https://www.ISRO.gov.in/news/"
    )

    assert result == "https://isro.gov.in/news"


def test_official_source_classification():
    result = get_source_metadata(
        "https://www.isro.gov.in"
    )

    assert result["domain"] == "isro.gov.in"
    assert result["source_category"] == "official"


def test_established_news_classification():
    result = get_source_metadata(
        "https://www.reuters.com/world/"
    )

    assert result["domain"] == "reuters.com"
    assert result["source_category"] == "established_news"


def test_unknown_source_classification():
    result = get_source_metadata(
        "https://example-blog.com/article"
    )

    assert result["domain"] == "example-blog.com"
    assert result["source_category"] == "unknown"


def test_invalid_url_classification():
    result = get_source_metadata("not-a-valid-url")

    assert result["domain"] is None
    assert result["source_category"] == "unknown"


def test_duplicate_search_results_are_removed():
    mock_response = MagicMock()

    mock_response.json.return_value = {
        "results": [
            {
                "title": "ISRO Mission Update",
                "url": "https://www.isro.gov.in/news/",
                "content": "ISRO announced a new space mission.",
                "published_date": "2026-10-30"
            },
            {
                "title": "ISRO Mission Update Duplicate",
                "url": "https://isro.gov.in/news",
                "content": "Duplicate article content.",
                "published_date": "2026-10-30"
            },
            {
                "title": "NASA Update",
                "url": "https://www.nasa.gov/news",
                "content": "NASA published a space mission update.",
                "published_date": "2026-10-29"
            }
        ]
    }

    mock_response.raise_for_status.return_value = None

    with patch(
        "app.search.SEARCH_API_KEY",
        "test-api-key"
    ), patch(
        "app.search.requests.post",
        return_value=mock_response
    ):

        results = fetch_live_news_evidence(
            "space mission updates",
            max_results=5
        )

    assert len(results) == 2
    assert results[0]["source_category"] == "official"
    assert results[1]["source_category"] == "official"


def test_empty_query_returns_empty_results():
    with patch(
        "app.search.SEARCH_API_KEY",
        "test-api-key"
    ):
        results = fetch_live_news_evidence("")

    assert results == []


# -----------------------------------------
# Verification query generation tests
# -----------------------------------------

def test_negated_claim_generates_three_queries():
    queries = generate_verification_queries(
        "Chandrayaan-3 failed to land on the Moon in August 2023."
    )

    assert len(queries) == 3

    assert "failed to" in queries[0].lower()

    assert "failed to" not in queries[1].lower()
    assert "outcome result" in queries[1].lower()

    assert "official statement news report" in queries[2].lower()


def test_positive_claim_keeps_original_query():
    claim = "Chandrayaan-3 landed on the Moon."

    queries = generate_verification_queries(claim)

    assert queries == [claim]


def test_empty_claim_generates_no_queries():
    assert generate_verification_queries("") == []


def test_whitespace_claim_generates_no_queries():
    assert generate_verification_queries("   ") == []


# -----------------------------------------
# Multi-query evidence retrieval tests
# -----------------------------------------

def test_fetch_claim_evidence_removes_duplicate_urls(monkeypatch):

    calls = []

    def mock_fetch(query, max_results=5):
        calls.append(query)

        if "failed to" in query.lower():
            return [
                {
                    "title": "Article A",
                    "url": "https://example.com/article",
                    "content": "Example article with enough content.",
                    "source_category": "unknown"
                }
            ]

        return [
            {
                "title": "Article A duplicate",
                "url": "https://www.example.com/article/",
                "content": "Duplicate article with enough content.",
                "source_category": "unknown"
            },
            {
                "title": "Article B",
                "url": "https://news.example.com/article",
                "content": "Another example article with enough content.",
                "source_category": "unknown"
            }
        ]

    monkeypatch.setattr(
        "app.search.fetch_live_news_evidence",
        mock_fetch
    )

    results = fetch_claim_evidence(
        "Chandrayaan-3 failed to land on the Moon.",
        max_results=5
    )

    # Three different search queries should be generated.
    assert len(calls) == 3

    # Duplicate URLs should be removed.
    assert len(results) == 2

    assert results[0]["url"] == "https://example.com/article"
    assert results[1]["url"] == "https://news.example.com/article"


def test_fetch_claim_evidence_prioritizes_official_sources(monkeypatch):

    def mock_fetch(query, max_results=5):
        return [
            {
                "title": "Unknown Blog",
                "url": "https://example-blog.com/article",
                "content": "Some relevant information.",
                "source_category": "unknown"
            },
            {
                "title": "ISRO Official Update",
                "url": "https://www.isro.gov.in/news",
                "content": "Official mission information.",
                "source_category": "official"
            },
            {
                "title": "Reuters Report",
                "url": "https://www.reuters.com/world/space",
                "content": "Independent news report.",
                "source_category": "established_news"
            }
        ]

    monkeypatch.setattr(
        "app.search.fetch_live_news_evidence",
        mock_fetch
    )

    results = fetch_claim_evidence(
        "Chandrayaan-3 landed on the Moon.",
        max_results=3
    )

    assert len(results) == 3

    assert results[0]["source_category"] == "official"
    assert results[1]["source_category"] == "established_news"
    assert results[2]["source_category"] == "unknown"


def test_fetch_claim_evidence_respects_max_results(monkeypatch):

    def mock_fetch(query, max_results=5):
        return [
            {
                "title": f"Article {i}",
                "url": f"https://example.com/article-{i}",
                "content": f"Content for article {i}.",
                "source_category": "unknown"
            }
            for i in range(1, 6)
        ]

    monkeypatch.setattr(
        "app.search.fetch_live_news_evidence",
        mock_fetch
    )

    results = fetch_claim_evidence(
        "Chandrayaan-3 landed on the Moon.",
        max_results=2
    )

    assert len(results) == 2
