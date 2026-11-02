from unittest.mock import patch, MagicMock

from app.search import (
    normalize_url,
    get_source_metadata,
    fetch_live_news_evidence
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

    assert result["domain"] == "www.reuters.com".removeprefix("www.")
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