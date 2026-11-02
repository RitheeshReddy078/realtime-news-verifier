from app.nlp_processor import (
    extract_sentences,
    filter_relevant_evidence
)

def test_extract_sentences():
    text = (
        "Chandrayaan-3 successfully landed on the Moon. "
        "India achieved this milestone in August 2023."
    )

    sentences = extract_sentences(text)

    assert len(sentences) == 2
    assert "Chandrayaan-3" in sentences[0]


def test_empty_articles_return_no_evidence():
    result = filter_relevant_evidence(
        "India launched Chandrayaan-3",
        [],
        threshold=0.50,
        top_k=5
    )

    assert result == []


def test_empty_claim_returns_no_evidence():
    result = filter_relevant_evidence(
        "",
        [
            {
                "title": "Example",
                "url": "https://example.com",
                "content": "This is an example article with enough text."
            }
        ]
    )

    assert result == []

def test_source_metadata_is_preserved_in_evidence(monkeypatch):
    import torch

    from app.nlp_processor import embedding_model

    def mock_encode(texts, **kwargs):
        if isinstance(texts, str):
            return torch.tensor([1.0, 0.0])

        return torch.tensor([[1.0, 0.0]])

    monkeypatch.setattr(
        embedding_model,
        "encode",
        mock_encode
    )

    articles = [
        {
            "title": "ISRO Mission Update",
            "url": "https://www.isro.gov.in/news",
            "content": (
                "Chandrayaan-3 successfully landed on the Moon."
            ),
            "domain": "isro.gov.in",
            "source_category": "official"
        }
    ]

    result = filter_relevant_evidence(
        "Chandrayaan-3 successfully landed on the Moon.",
        articles,
        threshold=0.50,
        top_k=5
    )

    assert len(result) == 1
    assert result[0]["source_domain"] == "isro.gov.in"
    assert result[0]["source_category"] == "official"
    assert result[0]["source_title"] == "ISRO Mission Update"