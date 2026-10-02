import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

def extract_text_from_url(url: str, timeout: int = 10) -> str:
    """
    Fetches raw HTML from a given URL and extracts clean readable text content.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements that clutter text extraction
        for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
            script_or_style.decompose()
            
        # Get clean text and remove excessive whitespace
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = ' '.join(chunk for chunk in chunks if chunk)
        
        return clean_text

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

if __name__ == "__main__":
    test_url = "https://en.wikipedia.org/wiki/List_of_ISRO_missions"
    print(f"Testing HTML/Text extraction for: {test_url}\n")
    
    extracted_content = extract_text_from_url(test_url)
    print(f"Successfully extracted {len(extracted_content)} characters of text.")
    print(f"Snippet preview: {extracted_content[:300]}...")