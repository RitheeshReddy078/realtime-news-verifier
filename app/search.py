import os
import requests

from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

load_dotenv()

SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")

# Domains that identify official organizations and government sources.
OFFICIAL_DOMAINS = {
    "isro.gov.in",
    "nasa.gov",
    "esa.int",
    "who.int",
    "un.org",
    "pib.gov.in",
    "india.gov.in",
}

# A small, maintainable list of established news publishers.
NEWS_DOMAINS = {
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "bbc.co.uk",
    "thehindu.com",
    "indianexpress.com",
    "ndtv.com",
    "theguardian.com",
    "cnn.com",
    "aljazeera.com",
    "hindustantimes.com",
}

def normalize_url(url: str) -> str:
    """Normalize URLs to help identify duplicate articles."""

    if not isinstance(url, str) or not url.strip():
        return ""

    try:
        parsed = urlparse(url.strip())

        if parsed.scheme.lower() not in {"http", "https"}:
            return ""

        if not parsed.hostname:
            return ""

        # Remove www and trailing slash.
        hostname = parsed.hostname.lower()
        hostname = hostname.removeprefix("www.")

        path = parsed.path.rstrip("/")

        # Ignore URL fragments, but preserve query parameters.
        normalized = urlunparse((
            parsed.scheme.lower(),
            hostname,
            path,
            "",
            parsed.query,
            ""
        ))

        return normalized

    except (ValueError, TypeError):
        return ""

def get_source_metadata(url: str) -> dict:
    """Identify the domain and classify the source."""

    normalized_url = normalize_url(url)

    if not normalized_url:
        return {
            "domain": None,
            "source_category": "unknown"
        }

    domain = urlparse(normalized_url).hostname

    is_official = (
        domain in OFFICIAL_DOMAINS
        or domain.endswith(".gov")
        or domain.endswith(".gov.in")
        or domain.endswith(".gov.uk")
        or domain.endswith(".gov.au")
        or domain.endswith(".mil")
        or domain.endswith(".int")
    )

    if is_official:
        category = "official"
    elif any(
        domain == known_domain
        or domain.endswith("." + known_domain)
        for known_domain in NEWS_DOMAINS
    ):
        category = "established_news"
    else:
        category = "unknown"

    return {
        "domain": domain,
        "source_category": category
    }

def fetch_live_news_evidence(
    query: str,
    max_results: int = 5
) -> list[dict]:
    """
    Retrieve real-time search results using Tavily.

    Removes duplicate article URLs and attaches source metadata.
    """

    if not SEARCH_API_KEY or SEARCH_API_KEY == "your_actual_tavily_api_key_here":
        raise ValueError(
            "Missing SEARCH_API_KEY in .env file. "
            "Please add your Tavily API key."
        )

    if not isinstance(query, str) or not query.strip():
        return []

    try:
        max_results = int(max_results)
    except (ValueError, TypeError):
        return []

    if max_results < 1:
        return []

    url = "https://api.tavily.com/search"

    payload = {
        "api_key": SEARCH_API_KEY,
        "query": query.strip(),
        "search_depth": "advanced",
        "max_results": min(max_results, 20)
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            return []

        results = data.get("results", [])

        if not isinstance(results, list):
            return []

        extracted_articles = []
        seen_urls = set()

        for item in results:

            if not isinstance(item, dict):
                continue

            article_url = item.get("url", "")
            normalized_url = normalize_url(article_url)

            # Ignore articles without a valid HTTP(S) URL.
            if not normalized_url:
                continue

            # Ignore duplicate articles.
            if normalized_url in seen_urls:
                continue

            seen_urls.add(normalized_url)

            title = item.get("title")
            content = item.get("content")

            title = (
                title.strip()
                if isinstance(title, str) and title.strip()
                else "No Title"
            )

            content = (
                content.strip()
                if isinstance(content, str)
                else ""
            )

            metadata = get_source_metadata(article_url)

            extracted_articles.append({
                "title": title,
                "url": article_url.strip(),
                "content": content,
                "published_date": item.get("published_date") or "N/A",
                "domain": metadata["domain"],
                "source_category": metadata["source_category"]
            })

        return extracted_articles

    except requests.exceptions.RequestException as e:
        print(f"Error fetching live search results: {e}")
        return []

    except (ValueError, TypeError) as e:
        print(f"Error processing search results: {e}")
        return []

if __name__ == "__main__":

    test_claim = "India space mission updates"

    print(f"Testing live search for: '{test_claim}'\n")

    articles = fetch_live_news_evidence(
        test_claim,
        max_results=3
    )

    print(f"Retrieved {len(articles)} unique sources:\n")

    for idx, article in enumerate(articles, 1):

        print(f"{idx}. {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   Domain: {article['domain']}")
        print(f"   Category: {article['source_category']}")
        print(f"   Published: {article['published_date']}")
        print(f"   Snippet: {article['content'][:150]}...\n")