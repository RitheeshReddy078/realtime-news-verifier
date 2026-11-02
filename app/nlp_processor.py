import re
import spacy
from sentence_transformers import SentenceTransformer, util

from app.search import get_source_metadata

# Load spaCy for sentence segmentation and linguistic analysis.
nlp = spacy.load("en_core_web_sm")

# Lightweight embedding model for semantic similarity.
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_sentences(text: str) -> list[str]:
    """Clean text and split it into meaningful sentences."""

    if not isinstance(text, str) or not text.strip():
        return []

    doc = nlp(text)
    sentences = []

    for sent in doc.sents:
        sentence = re.sub(r"\s+", " ", sent.text).strip()

        if len(sentence) > 15:
            sentences.append(sentence)

    return sentences

def filter_relevant_evidence(
    claim: str,
    articles: list[dict],
    threshold: float = 0.50,
    top_k: int = 5
) -> list[dict]:
    """
    Rank candidate sentences using semantic similarity.

    Carries source metadata from the search results into
    the final evidence dictionaries.
    """

    if not isinstance(claim, str) or not claim.strip():
        return []

    if not isinstance(articles, list) or not articles or top_k <= 0:
        return []

    # Collect candidate sentences and their source metadata.
    candidate_pool = []
    seen_sentences = set()

    for article in articles:
        if not isinstance(article, dict):
            continue

        title = article.get("title", "")
        url = article.get("url", "")
        content = article.get("content", "")

        title = title.strip() if isinstance(title, str) else ""
        url = url.strip() if isinstance(url, str) else ""

        # Use metadata supplied by search.py.
        # Derive it when processing older or manually supplied articles.
        metadata = get_source_metadata(url)

        domain = article.get("domain") or metadata["domain"]
        source_category = (
            article.get("source_category")
            or metadata["source_category"]
        )

        for sentence in extract_sentences(content):
            normalized_sentence = sentence.casefold()

            if normalized_sentence in seen_sentences:
                continue

            seen_sentences.add(normalized_sentence)

            candidate_pool.append({
                "sentence": sentence,
                "title": title or "Unknown source",
                "url": url,
                "domain": domain,
                "source_category": source_category
            })

    if not candidate_pool:
        return []

    # Encode claim and candidate sentences.
    claim_embedding = embedding_model.encode(
        claim,
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    sentence_list = [
        item["sentence"] for item in candidate_pool
    ]

    sentence_embeddings = embedding_model.encode(
        sentence_list,
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    # Calculate cosine similarity.
    similarity_scores = (
        util.cos_sim(claim_embedding, sentence_embeddings)[0]
        .cpu()
        .numpy()
    )

    ranked_evidence = []

    # Preserve the existing high similarity requirement.
    high_similarity_threshold = max(threshold + 0.25, 0.75)

    for idx, score in enumerate(similarity_scores):
        score = float(score)

        if score < high_similarity_threshold:
            continue

        candidate = candidate_pool[idx]

        ranked_evidence.append({
            "evidence_sentence": candidate["sentence"],
            "source_title": candidate["title"],
            "source_url": candidate["url"],
            "source_domain": candidate["domain"],
            "source_category": candidate["source_category"],
            "similarity_score": round(score, 4)
        })

    # Highest-scoring evidence first.
    ranked_evidence.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    # Limit evidence snippets per source.
    final_evidence = []
    source_counts = {}

    for item in ranked_evidence:
        source_url = item["source_url"] or item["source_title"]

        if source_counts.get(source_url, 0) >= 2:
            continue

        final_evidence.append(item)

        source_counts[source_url] = (
            source_counts.get(source_url, 0) + 1
        )

        if len(final_evidence) >= top_k:
            break

    return final_evidence

if __name__ == "__main__":
    from app.search import fetch_live_news_evidence

    test_claim = "ISRO plans multiple space missions"

    print(f"Testing NLP pipeline for claim: '{test_claim}'\n")

    raw_articles = fetch_live_news_evidence(
        test_claim,
        max_results=3
    )

    top_evidence = filter_relevant_evidence(
        test_claim,
        raw_articles,
        threshold=0.50,
        top_k=3
    )

    print(f"Extracted {len(top_evidence)} relevant evidence sentences:\n")

    if not top_evidence:
        print(
            "No sufficiently relevant evidence found. "
            "The claim should remain unverified until better evidence is retrieved."
        )

    for idx, item in enumerate(top_evidence, 1):
        print(f"{idx}. Score: {item['similarity_score']}")
        print(f"   Sentence: {item['evidence_sentence']}")
        print(f"   Source: {item['source_title']}")
        print(f"   Domain: {item['source_domain']}")
        print(f"   Category: {item['source_category']}")
        print(f"   URL: {item['source_url']}\n")