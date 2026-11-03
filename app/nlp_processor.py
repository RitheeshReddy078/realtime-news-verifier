
import re
import spacy

from sentence_transformers import SentenceTransformer, util

from app.search import get_source_metadata


# Load spaCy for sentence segmentation and linguistic analysis.
nlp = spacy.load("en_core_web_sm")

# Lightweight embedding model for semantic similarity.
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# Common words that do not contribute much to keyword relevance.
STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "be", "been", "being", "to", "of", "in", "on",
    "at", "by", "for", "from", "with", "and", "or",
    "but", "if", "it", "its", "this", "that", "these",
    "those", "as", "do", "does", "did", "has", "have",
    "had", "not", "no", "yes", "will", "would", "could",
    "should", "can", "may", "might", "must", "their",
    "there", "they", "them", "he", "she", "we", "you",
    "i", "me", "my", "our", "your", "who", "what",
    "when", "where", "why", "how"
}


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


def _get_claim_keywords(text: str) -> set[str]:
    """
    Extract meaningful keywords from a claim or sentence.

    Negation words are excluded from keyword overlap because
    positive and negative claims can describe the same event.
    """

    if not isinstance(text, str) or not text.strip():
        return set()

    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

    return {
        word
        for word in words
        if word not in STOP_WORDS and len(word) > 1
    }


def filter_relevant_evidence(
    claim: str,
    articles: list[dict],
    threshold: float = 0.50,
    top_k: int = 5
) -> list[dict]:
    """
    Rank candidate evidence sentences using:

    1. Semantic similarity.
    2. Keyword overlap.
    3. Source metadata.

    The function identifies relevant evidence, not whether
    that evidence supports or contradicts the claim.

    Final stance classification is handled by the RAG engine.
    """

    if not isinstance(claim, str) or not claim.strip():
        return []

    if not isinstance(articles, list) or not articles:
        return []

    try:
        threshold = float(threshold)
        top_k = int(top_k)
    except (ValueError, TypeError):
        return []

    if top_k <= 0 or not 0 <= threshold <= 1:
        return []

    # Extract meaningful claim keywords.
    claim_keywords = _get_claim_keywords(claim)

    # Collect candidate sentences and source metadata.
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

    # Encode the claim and candidate sentences.
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

    for idx, score in enumerate(similarity_scores):

        similarity_score = float(score)

        candidate = candidate_pool[idx]

        # Calculate keyword overlap.
        sentence_keywords = _get_claim_keywords(
            candidate["sentence"]
        )

        if claim_keywords:
            overlap_count = len(
                claim_keywords.intersection(sentence_keywords)
            )

            keyword_overlap = (
                overlap_count / len(claim_keywords)
            )
        else:
            keyword_overlap = 0.0

        # Keep evidence if it meets either:
        # 1. The semantic similarity threshold.
        # 2. A reasonable keyword overlap with some semantic relevance.
        is_semantically_relevant = (
            similarity_score >= threshold
        )

        is_keyword_relevant = (
            keyword_overlap >= 0.35
            and similarity_score >= max(0.20, threshold - 0.15)
        )

        if not (
            is_semantically_relevant
            or is_keyword_relevant
        ):
            continue

        # Combine similarity and keyword overlap for ranking.
        relevance_score = (
            0.70 * similarity_score
            + 0.30 * keyword_overlap
        )

        ranked_evidence.append({
            "evidence_sentence": candidate["sentence"],
            "source_title": candidate["title"],
            "source_url": candidate["url"],
            "source_domain": candidate["domain"],
            "source_category": candidate["source_category"],
            "similarity_score": round(similarity_score, 4),
            "keyword_overlap": round(keyword_overlap, 4),
            "relevance_score": round(relevance_score, 4)
        })

    # Highest combined relevance first.
    ranked_evidence.sort(
        key=lambda item: item["relevance_score"],
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

    from app.search import fetch_claim_evidence

    test_claim = (
        "Chandrayaan-3 failed to land on the Moon "
        "in August 2023."
    )

    print(f"Testing NLP pipeline for claim:\n{test_claim}\n")

    raw_articles = fetch_claim_evidence(
        test_claim,
        max_results=5
    )

    print(f"Retrieved {len(raw_articles)} articles.\n")

    top_evidence = filter_relevant_evidence(
        test_claim,
        raw_articles,
        threshold=0.50,
        top_k=5
    )

    print(
        f"Extracted {len(top_evidence)} relevant "
        "evidence sentences:\n"
    )

    if not top_evidence:
        print(
            "No sufficiently relevant evidence found. "
            "The claim should remain unverified until "
            "better evidence is retrieved."
        )

    for idx, item in enumerate(top_evidence, 1):

        print(f"{idx}. Relevance: {item['relevance_score']}")
        print(f"   Similarity: {item['similarity_score']}")
        print(f"   Keyword overlap: {item['keyword_overlap']}")
        print(f"   Sentence: {item['evidence_sentence']}")
        print(f"   Source: {item['source_title']}")
        print(f"   Domain: {item['source_domain']}")
        print(f"   Category: {item['source_category']}")
        print(f"   URL: {item['source_url']}\n")
