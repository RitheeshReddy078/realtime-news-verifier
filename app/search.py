import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")

def fetch_live_news_evidence(query: str, max_results: int = 5) -> list[dict]:
    """
    Retrieves real-time search results for a given news claim using the Tavily Search API.
    """
    if not SEARCH_API_KEY or SEARCH_API_KEY == "your_actual_tavily_api_key_here":
        raise ValueError("Missing SEARCH_API_KEY in .env file. Please add your Tavily API key.")

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": SEARCH_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        
        extracted_articles = []
        for item in results:
            extracted_articles.append({
                "title": item.get("title", "No Title"),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "published_date": item.get("published_date", "N/A")
            })
        return extracted_articles
    except requests.exceptions.RequestException as e:
        print(f"Error fetching live search results: {e}")
        return []

if __name__ == "__main__":
    # Test execution
    test_claim = "India space mission updates"
    print(f"Testing live search for: '{test_claim}'...\n")
    articles = fetch_live_news_evidence(test_claim, max_results=3)
    
    print(f"Retrieved {len(articles)} sources:\n")
    for idx, article in enumerate(articles, 1):
        print(f"{idx}. {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   Snippet: {article['content'][:150]}...\n")