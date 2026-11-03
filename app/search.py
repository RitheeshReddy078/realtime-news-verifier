
import os
import re
import requests

from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

load_dotenv()

SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")

# Official organizations and government sources.
OFFICIAL_DOMAINS = {
    "isro.gov.in",
    "nasa.gov",
    "esa.int",
    "who.int",
    "un.org",
    "pib.gov.in",
    "india.gov.in",
}

# Established news publishers.
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
    """Normalize URLs to identify duplicate articles."""

    if not isinstance(url, str) or not url.strip():
        return ""

    try:
        parsed = urlparse(url.strip())

        if parsed.scheme.lower() not in {"http", "https"}:
            return ""

        if not parsed.hostname:
            return ""

        hostname = parsed.hostname.lower().removeprefix("www.")
        path = parsed.path.rstrip("/")

        return urlunparse((
            parsed.scheme.lower(),
            hostname,
            path,
            "",
            parsed.query,
            ""
        ))

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


def generate_verification_queries(claim: str) -> list[str]:
    """
    Generate multiple search perspectives.

    Alternative queries improve search recall. They do not
    determine whether the original claim is true or false.
    """

    if not isinstance(claim, str) or not claim.strip():
        return []

    original_query = " ".join(claim.split())
    queries = [original_query]

    negation_patterns = [
        r"\bfailed to\b",
        r"\bfails to\b",
        r"\bdid not\b",
        r"\bdoes not\b",
        r"\bdo not\b",
        r"\bhas not\b",
        r"\bhave not\b",
        r"\bhad not\b",
        r"\bwas not\b",
        r"\bwere not\b",
        r"\bis not\b",
        r"\bare not\b",
        r"\bwill not\b",
        r"\bcannot\b",
        r"\bnever\b",
        r"\bnot\b",
    ]

    alternative_query = original_query

    for pattern in negation_patterns:
        alternative_query = re.sub(
            pattern,
            " ",
            alternative_query,
            flags=re.IGNORECASE
        )

    alternative_query = " ".join(alternative_query.split())

    if (
        alternative_query
        and alternative_query.casefold() != original_query.casefold()
        and len(alternative_query) >= 5
    ):
        queries.append(f"{alternative_query} outcome result")
        queries.append(
            f"{alternative_query} official statement news report"
        )

    unique_queries = []
    seen = set()

    for query in queries:
        key = query.casefold()

        if key not in seen:
            seen.add(key)
            unique_queries.append(query)

    return unique_queries


def fetch_live_news_evidence(
    query: str,
    max_results: int = 5
) -> list[dict]:
    """Retrieve live search results using Tavily."""

    if (
        not SEARCH_API_KEY
        or SEARCH_API_KEY == "your_actual_tavily_api_key_here"
    ):
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

            if not normalized_url or normalized_url in seen_urls:
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


def _select_diverse_articles(
    articles: list[dict],
    max_results: int
) -> list[dict]:
    """
    Select articles by source priority while preferring
    different domains before selecting another article
    from a domain already represented.

    Domain diversity is not proof of source independence.
    """

    source_priority = {
        "official": 2,
        "established_news": 1,
        "unknown": 0
    }

    ranked = sorted(
        articles,
        key=lambda article: source_priority.get(
            article.get("source_category", "unknown"),
            0
        ),
        reverse=True
    )

    selected = []
    selected_urls = set()
    selected_domains = set()

    # First pass: prefer one article per domain.
    for article in ranked:

        if len(selected) >= max_results:
            break

        normalized_url = normalize_url(article.get("url", ""))

        if not normalized_url or normalized_url in selected_urls:
            continue

        domain = article.get("domain")

        if not isinstance(domain, str) or not domain.strip():
            domain = get_source_metadata(
                article.get("url", "")
            ).get("domain")

        domain = domain.lower().removeprefix("www.") if domain else None

        if domain and domain in selected_domains:
            continue

        selected.append(article)
        selected_urls.add(normalized_url)

        if domain:
            selected_domains.add(domain)

    # Second pass: fill remaining places with other unique URLs.
    if len(selected) < max_results:

        for article in ranked:

            if len(selected) >= max_results:
                break

            normalized_url = normalize_url(article.get("url", ""))

            if not normalized_url or normalized_url in selected_urls:
                continue

            selected.append(article)
            selected_urls.add(normalized_url)

    return selected


def fetch_claim_evidence(
    claim: str,
    max_results: int = 5
) -> list[dict]:
    """
    Retrieve evidence from multiple search perspectives.

    Results are combined, deduplicated and selected with
    source priority and domain diversity in mind.

    max_results is the final number of unique articles returned.
    """

    if not isinstance(claim, str) or not claim.strip():
        return []

    try:
        max_results = int(max_results)
    except (ValueError, TypeError):
        return []

    if max_results < 1:
        return []

    queries = generate_verification_queries(claim)

    if not queries:
        return []

    all_articles = []
    seen_urls = set()

    for query in queries:

        articles = fetch_live_news_evidence(
            query,
            max_results=max_results
        )

        for article in articles:

            if not isinstance(article, dict):
                continue

            normalized_url = normalize_url(
                article.get("url", "")
            )

            if not normalized_url or normalized_url in seen_urls:
                continue

            seen_urls.add(normalized_url)
            all_articles.append(article)

    return _select_diverse_articles(
        all_articles,
        max_results
    )


if __name__ == "__main__":

    test_claim = (
        "Chandrayaan-3 failed to land on the Moon "
        "in August 2023."
    )

    print(f"Testing verification search for:\n{test_claim}\n")

    queries = generate_verification_queries(test_claim)

    print("Generated search queries:")

    for idx, query in enumerate(queries, 1):
        print(f"{idx}. {query}")

    print("\nRetrieving combined evidence...\n")

    articles = fetch_claim_evidence(
        test_claim,
        max_results=5
    )

    print(f"Retrieved {len(articles)} unique articles:\n")

    for idx, article in enumerate(articles, 1):

        print(f"{idx}. {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   Domain: {article['domain']}")
        print(f"   Category: {article['source_category']}")
        print(f"   Published: {article['published_date']}")
        print(f"   Snippet: {article['content'][:150]}...\n")
