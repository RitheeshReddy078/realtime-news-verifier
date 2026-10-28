
import re
import spacy
import numpy as np
from sentence_transformers import SentenceTransformer, util


# Load spaCy for sentence segmentation and linguistic analysis.
nlp = spacy.load("en_core_web_sm")

# Lightweight embedding model for semantic similarity.
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_sentences(text: str) -> list[str]:
    """
    Clean text and split it into meaningful sentences.
    Ignore empty and excessively short fragments.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    doc = nlp(text)
    sentences = []

    for sent in doc.sents:
        sentence = re.sub(r"\s+", " ", sent.text).strip()

        if len(sentence) > 15:
            sentences.append(sentence)

    return sentences


def _get_claim_keywords(claim: str) -> set[str]:
    """
    Extract meaningful words from a claim.

    These keywords help prevent sentences about the same general
    topic from being accepted as evidence for a specific claim.
    """
    doc = nlp(claim)
    keywords = set()

    for token in doc:
        if (
            not token.is_stop
            and not token.is_punct
            and not token.is_space
            and len(token.text) > 2
            and token.is_alpha
        ):
            keywords.add(token.lemma_.lower())

    return keywords


def filter_relevant_evidence(
    claim: str,
    articles: list[dict],
    threshold: float = 0.50,
    top_k: int = 5
) -> list[dict]:
    """
    Rank candidate sentences using semantic similarity and
    claim-keyword overlap.

    A sentence is accepted when:
    1. It meets the minimum similarity threshold.
    2. It shares meaningful keywords with the claim, or has
       exceptionally high semantic similarity.

    Duplicate sentences are removed, and results are limited
    per source so one article cannot dominate the evidence list.

    Returns dictionaries compatible with the existing main.py
    and rag_engine.py.
    """
    if not isinstance(claim, str) or not claim.strip():
        return []

    if not articles or top_k <= 0:
        return []

    claim_keywords = _get_claim_keywords(claim)

    # Collect candidate sentences and their source metadata.
    candidate_pool = []
    seen_sentences = set()

    for article in articles:
        if not isinstance(article, dict):
            continue

        title = article.get("title", "") or ""
        url = article.get("url", "") or ""
        content = article.get("content", "") or ""

        for sentence in extract_sentences(content):
            normalized_sentence = sentence.casefold()

            if normalized_sentence in seen_sentences:
                continue

            seen_sentences.add(normalized_sentence)

            candidate_pool.append({
                "sentence": sentence,
                "title": title,
                "url": url
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

    # Exceptionally high similarity can allow paraphrases that
    # use different words, but it is not proof that a claim is true.
    high_similarity_threshold = max(threshold + 0.25, 0.75)

    for idx, score in enumerate(similarity_scores):
        score = float(score)

        if score < threshold:
            continue

        candidate = candidate_pool[idx]
        sentence_doc = nlp(candidate["sentence"])

        sentence_keywords = {
            token.lemma_.lower()
            for token in sentence_doc
            if (
                not token.is_stop
                and not token.is_punct
                and not token.is_space
                and len(token.text) > 2
                and token.is_alpha
            )
        }

        keyword_overlap = claim_keywords.intersection(
            sentence_keywords
        )

        # Require stronger semantic relevance.
        # Keyword overlap alone is not sufficient evidence.
        if score < high_similarity_threshold:
            continue

        ranked_evidence.append({
            "evidence_sentence": candidate["sentence"],
            "source_title": candidate["title"],
            "source_url": candidate["url"],
            "similarity_score": round(score, 4)
        })

    # Highest-scoring evidence first.
    ranked_evidence.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    # Limit the number of snippets taken from each source.
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

    print(f"Testing NLP pipeline for claim: '{test_claim}'...\n")

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

    print(
        f"Extracted {len(top_evidence)} relevant evidence "
        "sentences:\n"
    )

    if not top_evidence:
        print(
            "No sufficiently relevant evidence found. "
            "The claim should remain unverified until better "
            "evidence is retrieved."
        )

    for idx, item in enumerate(top_evidence, 1):
        print(f"{idx}. Score: {item['similarity_score']}")
        print(f"   Sentence: {item['evidence_sentence']}")
        print(
            f"   Source: {item['source_title']} "
            f"({item['source_url']})\n"
        )
