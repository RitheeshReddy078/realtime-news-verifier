from app.rag_engine import (
    clean_evidence,
    validate_llm_response,
    analyze_claim_with_llm
)

def test_duplicate_evidence_is_removed():
    evidence = [
        {
            "evidence_sentence": "Chandrayaan-3 successfully landed on the Moon.",
            "source_title": "ISRO",
            "source_url": "https://isro.gov.in/news"
        },
        {
            "evidence_sentence": "Chandrayaan-3 successfully landed on the Moon.",
            "source_title": "ISRO",
            "source_url": "https://isro.gov.in/news"
        }
    ]

    cleaned, sources = clean_evidence(evidence)

    assert len(cleaned) == 1
    assert len(sources) == 1

def test_duplicate_source_urls_are_removed():
    evidence = [
        {
            "evidence_sentence": "Chandrayaan-3 successfully landed on the Moon.",
            "source_title": "ISRO",
            "source_url": "https://isro.gov.in/news"
        },
        {
            "evidence_sentence": "India achieved a historic lunar landing.",
            "source_title": "ISRO News",
            "source_url": "https://isro.gov.in/news/"
        }
    ]

    cleaned, sources = clean_evidence(evidence)

    assert len(cleaned) == 2
    assert len(sources) == 1

def test_invalid_evidence_is_ignored():
    evidence = [
        None,
        {},
        {
            "evidence_sentence": "Short",
            "source_title": "Example",
            "source_url": "https://example.com"
        },
        {
            "evidence_sentence": "Chandrayaan-3 successfully landed on the Moon.",
            "source_title": None,
            "source_url": None
        }
    ]

    cleaned, sources = clean_evidence(evidence)

    assert len(cleaned) == 1
    assert cleaned[0]["source_title"] == "Unknown source"
    assert sources == []

def test_invalid_verdict_becomes_unverified():
    result = validate_llm_response(
        {
            "verdict": "MAYBE",
            "confidence_score": 95,
            "explanation": "The evidence is unclear.",
            "past_events": [{"event": "Unknown event"}],
            "current_and_future_updates": []
        },
        []
    )

    assert result["verdict"] == "UNVERIFIED"
    assert result["confidence_score"] == 20
    assert result["past_events"] == []

def test_confidence_score_is_limited_to_100():
    result = validate_llm_response(
        {
            "verdict": "SUPPORTED",
            "confidence_score": 150,
            "explanation": "The evidence supports the claim.",
            "past_events": [],
            "current_and_future_updates": []
        },
        []
    )

    assert result["confidence_score"] == 100

def test_missing_evidence_returns_unverified():
    result = analyze_claim_with_llm(
        "Chandrayaan-3 landed on the Moon.",
        []
    )

    assert result["verdict"] == "UNVERIFIED"
    assert result["confidence_score"] == 0
    assert result["sources"] == []

def test_supporting_evidence_classification():
    result = validate_llm_response(
        {
            "verdict": "SUPPORTED",
            "confidence_score": 90,
            "explanation": "The evidence supports the claim.",
            "evidence_analysis": [
                {
                    "evidence_index": 1,
                    "stance": "SUPPORTING",
                    "reasoning": "Directly supports the claim."
                }
            ],
            "past_events": [],
            "current_and_future_updates": []
        },
        [],
        evidence_count=1
    )

    assert result["evidence_analysis"][0]["stance"] == "SUPPORTING"

def test_contradicting_evidence_classification():
    result = validate_llm_response(
        {
            "verdict": "CONTRADICTED",
            "confidence_score": 90,
            "explanation": "The evidence contradicts the claim.",
            "evidence_analysis": [
                {
                    "evidence_index": 1,
                    "stance": "CONTRADICTING",
                    "reasoning": "Directly conflicts with the claim."
                }
            ],
            "past_events": [],
            "current_and_future_updates": []
        },
        [],
        evidence_count=1
    )

    assert result["evidence_analysis"][0]["stance"] == "CONTRADICTING"

def test_contextual_evidence_classification():
    result = validate_llm_response(
        {
            "verdict": "UNVERIFIED",
            "confidence_score": 10,
            "explanation": "The evidence is contextual only.",
            "evidence_analysis": [
                {
                    "evidence_index": 1,
                    "stance": "CONTEXTUAL",
                    "reasoning": "Related but does not establish the claim."
                }
            ],
            "past_events": [],
            "current_and_future_updates": []
        },
        [],
        evidence_count=1
    )

    assert result["evidence_analysis"][0]["stance"] == "CONTEXTUAL"

def test_invalid_evidence_stance_becomes_contextual():
    result = validate_llm_response(
        {
            "verdict": "UNVERIFIED",
            "confidence_score": 10,
            "explanation": "Insufficient evidence.",
            "evidence_analysis": [
                {
                    "evidence_index": 1,
                    "stance": "MAYBE",
                    "reasoning": "Unclear classification."
                }
            ],
            "past_events": [],
            "current_and_future_updates": []
        },
        [],
        evidence_count=1
    )

    assert result["evidence_analysis"][0]["stance"] == "CONTEXTUAL"

def test_invalid_evidence_index_is_ignored():
    result = validate_llm_response(
        {
            "verdict": "UNVERIFIED",
            "confidence_score": 10,
            "explanation": "Insufficient evidence.",
            "evidence_analysis": [
                {
                    "evidence_index": 5,
                    "stance": "SUPPORTING",
                    "reasoning": "Invalid index."
                }
            ],
            "past_events": [],
            "current_and_future_updates": []
        },
        [],
        evidence_count=1
    )

    assert result["evidence_analysis"] == []