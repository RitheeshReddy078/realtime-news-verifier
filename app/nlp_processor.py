import spacy
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Load spaCy model for sentence segmentation
nlp = spacy.load("en_core_web_sm")

# Load lightweight, fast embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_sentences(text: str) -> list[str]:
    """
    Cleans text and splits it into individual sentences using spaCy.
    """
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 15]
    return sentences

def filter_relevant_evidence(claim: str, articles: list[dict], threshold: float = 0.35, top_k: int = 5) -> list[dict]:
    """
    Ranks sentences from retrieved articles against the user claim using cosine similarity.
    Returns the top matching evidence snippets.
    """
    if not articles:
        return []

    # Collect all candidate sentences with their source metadata
    candidate_pool = []
    for article in articles:
        sentences = extract_sentences(article.get("content", ""))
        for sentence in sentences:
            candidate_pool.append({
                "sentence": sentence,
                "title": article.get("title", ""),
                "url": article.get("url", "")
            })

    if not candidate_pool:
        return []

    # Compute embeddings
    claim_embedding = embedding_model.encode(claim, convert_to_tensor=True)
    sentence_list = [item["sentence"] for item in candidate_pool]
    sentence_embeddings = embedding_model.encode(sentence_list, convert_to_tensor=True)

    # Compute cosine similarity
    similarity_scores = util.cos_sim(claim_embedding, sentence_embeddings)[0].cpu().numpy()

    # Filter and rank evidence
    ranked_evidence = []
    for idx, score in enumerate(similarity_scores):
        if score >= threshold:
            ranked_evidence.append({
                "evidence_sentence": candidate_pool[idx]["sentence"],
                "source_title": candidate_pool[idx]["title"],
                "source_url": candidate_pool[idx]["url"],
                "similarity_score": round(float(score), 4)
            })

    # Sort descending by similarity score and take top_k
    ranked_evidence = sorted(ranked_evidence, key=lambda x: x["similarity_score"], reverse=True)[:top_k]
    return ranked_evidence

if __name__ == "__main__":
    # Test execution combining Search + NLP
    from app.search import fetch_live_news_evidence

    test_claim = "ISRO plans multiple space missions"
    print(f"Testing NLP pipeline for claim: '{test_claim}'...\n")

    raw_articles = fetch_live_news_evidence(test_claim, max_results=3)
    top_evidence = filter_relevant_evidence(test_claim, raw_articles, threshold=0.30, top_k=3)

    print(f"Extracted {len(top_evidence)} top relevant evidence sentences:\n")
    for idx, item in enumerate(top_evidence, 1):
        print(f"{idx}. Score: {item['similarity_score']}")
        print(f"   Sentence: \"{item['evidence_sentence']}\"")
        print(f"   Source: {item['source_title']} ({item['source_url']})\n")