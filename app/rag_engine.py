import os
import json
import time
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")

def check_gemini_health():
    """
    Check Gemini API connectivity without generating content.
    """

    if not LLM_API_KEY or LLM_API_KEY == "your_actual_openai_or_gemini_api_key_here":
        return "unavailable"

    try:
        client = genai.Client(api_key=LLM_API_KEY)

        # Check whether the configured primary model is accessible.
        client.models.get(model="gemini-3.6-flash")

        return "operational"

    except Exception as e:
        print(f"Gemini health check failed: {type(e).__name__}: {e}")
        return "unavailable"

VALID_VERDICTS = {
    "SUPPORTED",
    "CONTRADICTED",
    "MISLEADING",
    "UNVERIFIED"
}

VALID_STANCES = {
    "SUPPORTING",
    "CONTRADICTING",
    "CONTEXTUAL"
}


def create_fallback_report(explanation, sources=None):
    """Create a consistent fallback response."""

    return {
        "verdict": "UNVERIFIED",
        "confidence_score": 0,
        "explanation": explanation,
        "past_events": [],
        "current_and_future_updates": [],
        "sources": sources or [],
        "evidence_analysis": []
    }


def clean_evidence(evidence_list):
    """
    Remove invalid and duplicate evidence sentences.
    Preserve source metadata and collect unique sources.
    """

    cleaned_evidence = []
    seen_sentences = set()
    seen_urls = set()
    sources = []

    for item in evidence_list:
        if not isinstance(item, dict):
            continue

        sentence = item.get("evidence_sentence")

        if not isinstance(sentence, str):
            continue

        sentence = " ".join(sentence.split())

        if len(sentence) < 15:
            continue

        sentence_key = sentence.casefold()

        if sentence_key in seen_sentences:
            continue

        seen_sentences.add(sentence_key)

        title = item.get("source_title")
        url = item.get("source_url")
        domain = item.get("source_domain")
        category = item.get("source_category")

        title = title.strip() if isinstance(title, str) else ""
        url = url.strip() if isinstance(url, str) else ""
        domain = domain.strip() if isinstance(domain, str) else ""
        category = category.strip() if isinstance(category, str) else ""

        cleaned_item = {
            "evidence_sentence": sentence,
            "source_title": title or "Unknown source",
            "source_url": url,
            "source_domain": domain or None,
            "source_category": category or "unknown"
        }

        cleaned_evidence.append(cleaned_item)

        # Keep each source URL only once.
        if url:
            url_key = url.rstrip("/").casefold()

            if url_key not in seen_urls:
                seen_urls.add(url_key)

                sources.append({
                    "title": title or "Unknown source",
                    "url": url,
                    "domain": domain or None,
                    "source_category": category or "unknown"
                })

    return cleaned_evidence, sources


def validate_llm_response(
    parsed_result,
    sources,
    evidence_count=None
):
    """Validate and normalize Gemini's JSON response."""

    if not isinstance(parsed_result, dict):
        raise ValueError("Gemini response must be a JSON object.")

    verdict = parsed_result.get("verdict", "UNVERIFIED")

    if not isinstance(verdict, str):
        verdict = "UNVERIFIED"

    verdict = verdict.strip().upper()

    if verdict not in VALID_VERDICTS:
        verdict = "UNVERIFIED"

    confidence = parsed_result.get("confidence_score", 0)

    try:
        confidence = int(float(confidence))
    except (ValueError, TypeError):
        confidence = 0

    confidence = max(0, min(100, confidence))

    explanation = parsed_result.get("explanation", "")

    if not isinstance(explanation, str):
        explanation = "The claim could not be reliably evaluated."

    past_events = parsed_result.get("past_events", [])
    updates = parsed_result.get("current_and_future_updates", [])

    if not isinstance(past_events, list):
        past_events = []

    if not isinstance(updates, list):
        updates = []

    # Validate individual evidence classifications.
    evidence_analysis = parsed_result.get(
        "evidence_analysis", []
    )

    if not isinstance(evidence_analysis, list):
        evidence_analysis = []

    validated_analysis = []
    seen_indices = set()

    for item in evidence_analysis:

        if not isinstance(item, dict):
            continue

        evidence_index = item.get("evidence_index")

        # Evidence index must be an integer.
        # Boolean values are excluded because bool is a subclass of int.
        if (
            not isinstance(evidence_index, int)
            or isinstance(evidence_index, bool)
        ):
            continue

        # Check that the index exists in the cleaned evidence list.
        if evidence_index < 1:
            continue

        if (
            evidence_count is not None
            and evidence_index > evidence_count
        ):
            continue

        # Prevent duplicate evidence indices.
        if evidence_index in seen_indices:
            continue

        stance = item.get("stance", "CONTEXTUAL")

        if not isinstance(stance, str):
            stance = "CONTEXTUAL"

        stance = stance.strip().upper()

        if stance not in VALID_STANCES:
            stance = "CONTEXTUAL"

        reasoning = item.get("reasoning", "")

        if not isinstance(reasoning, str):
            reasoning = ""

        validated_analysis.append({
            "evidence_index": evidence_index,
            "stance": stance,
            "reasoning": reasoning
        })

        seen_indices.add(evidence_index)

    # An UNVERIFIED result must not contain confident conclusions.
    if verdict == "UNVERIFIED":
        confidence = min(confidence, 20)
        past_events = []
        updates = []

    return {
        "verdict": verdict,
        "confidence_score": confidence,
        "explanation": explanation,
        "past_events": past_events,
        "current_and_future_updates": updates,
        "sources": sources,
        "evidence_analysis": validated_analysis
    }


def analyze_claim_with_llm(
    claim: str,
    evidence_list: list[dict]
) -> dict:
    """
    Analyze a claim against retrieved evidence using Gemini.

    Classifies evidence as SUPPORTING, CONTRADICTING,
    or CONTEXTUAL before producing the final verdict.
    """

    if (
        not LLM_API_KEY
        or LLM_API_KEY == "your_actual_openai_or_gemini_api_key_here"
    ):
        return create_fallback_report(
            "LLM API Key missing in .env file."
        )

    if not isinstance(claim, str) or not claim.strip():
        return create_fallback_report(
            "A valid claim is required for verification."
        )

    if not isinstance(evidence_list, list):
        return create_fallback_report(
            "The evidence data is invalid."
        )

    cleaned_evidence, sources = clean_evidence(evidence_list)

    if not cleaned_evidence:
        return create_fallback_report(
            "We could not find sufficient relevant evidence to confirm "
            "or contradict this claim. This does not mean the claim is "
            "false; the available evidence is inconclusive. Check reliable "
            "primary sources or try again later.",
            sources
        )

    today_str = datetime.now().strftime("%B %d, %Y")

    # Format evidence with numbered indices and source metadata.
    formatted_evidence = ""

    for idx, item in enumerate(cleaned_evidence, 1):

        formatted_evidence += (
            f'Evidence {idx}: "{item["evidence_sentence"]}" '
            f'(Source: {item["source_title"]}; '
            f'Domain: {item.get("source_domain") or "Unknown"}; '
            f'Category: {item.get("source_category", "unknown")})\n'
        )

    prompt = f"""
You are an expert AI Time-Aware News Verification System.

TODAY'S DATE: {today_str}

USER CLAIM:
"{claim}"

RETRIEVED EVIDENCE:
{formatted_evidence}

INSTRUCTIONS:

1. Evaluate every evidence sentence individually in relation
   to the exact user claim.

2. Classify each evidence sentence using exactly one category:

   SUPPORTING:
   The sentence provides information that directly supports the claim.

   CONTRADICTING:
   The sentence provides information that directly conflicts
   with the claim.

   CONTEXTUAL:
   The sentence is related to the topic but does not clearly
   support or contradict the claim.

3. Do not confuse semantic similarity with agreement.
   A sentence can be highly relevant while contradicting the claim.

4. Consider negation, dates, quantities, locations, event status,
   and important missing context.

5. Return SUPPORTED only when reliable evidence directly supports
   the claim.

6. Return CONTRADICTED only when reliable evidence directly
   contradicts the claim.

7. Return MISLEADING when the claim substantially misrepresents
   the available evidence or omits important context.

8. Return UNVERIFIED when evidence is insufficient, indirect,
   weak, unrelated, or inconclusive.

9. Do not treat the absence of evidence as proof that a claim is false.

10. Do not invent events, dates, announcements, or future updates.

11. Source categories provide context, not proof of truth.
    An official source is not automatically correct, and an unknown
    source is not automatically false.

12. Confidence must reflect evidence quality, relevance,
    agreement, and source diversity.

13. If evidence is insufficient, use a low confidence score
    between 0 and 20.

14. Classify every supplied evidence item exactly once.
    Use its numbered Evidence index.

15. Keep your reasoning concise and grounded in the actual sentence.

16. Return valid JSON only. Do not include Markdown or explanations
    outside the JSON object.

OUTPUT SCHEMA:

{{
    "verdict": "SUPPORTED|CONTRADICTED|MISLEADING|UNVERIFIED",
    "confidence_score": 90,
    "explanation": "A concise explanation based on the evidence.",
    "evidence_analysis": [
        {{
            "evidence_index": 1,
            "stance": "SUPPORTING",
            "reasoning": "This sentence directly supports the claim."
        }}
    ],
    "past_events": [
        {{
            "event": "Description of past action",
            "date": "Exact or approximate date",
            "relative_time": "Earlier in 2026"
        }}
    ],
    "current_and_future_updates": [
        {{
            "update": "Upcoming launch or current active status",
            "expected_timeframe": "Target date or timeframe"
        }}
    ]
}}
"""

    # Primary model was tested successfully with your API key.
    # Other models are fallbacks, not guaranteed to be available.
    candidate_models = [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest",
        "gemini-flash-lite-latest"
    ]

    try:
        client = genai.Client(api_key=LLM_API_KEY)
    except Exception as e:
        return create_fallback_report(
            f"Could not initialize Gemini client: {str(e)}",
            sources
        )

    last_error = None

    for model_name in candidate_models:

        try:
            print(f"Trying Gemini model: {model_name}")

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            if not response.text:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            parsed_result = json.loads(response.text)

            # Validate Gemini's response and return it directly.
            # No rigid two-domain rule is applied here.
            result = validate_llm_response(
                parsed_result,
                sources,
                evidence_count=len(cleaned_evidence)
            )

            print(f"Gemini analysis successful using {model_name}")

            return result

        except Exception as e:
            last_error = e

            print(
                f"Gemini model {model_name} failed: {str(e)}"
            )

            # Brief pause before trying the next fallback model.
            if model_name != candidate_models[-1]:
                time.sleep(1)

    print(
        "Error calling LLM after trying fallback models:",
        last_error
    )

    return create_fallback_report(
        f"Failed to perform LLM analysis after trying available models: "
        f"{str(last_error)}",
        sources
    )


if __name__ == "__main__":

    from app.search import fetch_live_news_evidence
    from app.nlp_processor import filter_relevant_evidence

    test_claim = "ISRO space mission launches"

    print(
        f"Running Time-Aware Verification for claim: "
        f"'{test_claim}'...\n"
    )

    articles = fetch_live_news_evidence(
        test_claim,
        max_results=3
    )

    evidence = filter_relevant_evidence(
        test_claim,
        articles,
        threshold=0.30,
        top_k=3
    )

    report = analyze_claim_with_llm(
        test_claim,
        evidence
    )

    print("=" * 60)
    print("TIME-AWARE VERIFICATION REPORT")
    print("=" * 60)

    print(f"VERDICT: {report.get('verdict')}")
    print(f"CONFIDENCE: {report.get('confidence_score')}%")

    print("\nEXPLANATION:")
    print(report.get("explanation"))

    print("\nEVIDENCE ANALYSIS:")

    for item in report.get("evidence_analysis", []):

        print(
            f" - Evidence {item.get('evidence_index')}: "
            f"{item.get('stance')}"
        )

        print(f"   Reason: {item.get('reasoning')}")

    print("\nPAST VERIFIED EVENTS:")

    for item in report.get("past_events", []):

        print(f" - {item.get('event')}")

        print(
            f"   Date: {item.get('date')} "
            f"({item.get('relative_time')})"
        )

    print("\nCURRENT AND UPCOMING UPDATES:")

    for item in report.get("current_and_future_updates", []):

        print(f" - {item.get('update')}")

        print(
            f"   Timeframe: {item.get('expected_timeframe')}"
        )

    print("\nVERIFIED SOURCES:")

    for source in report.get("sources", []):

        print(f" - {source.get('title')}")
        print(f"   URL: {source.get('url')}")
        print(f"   Domain: {source.get('domain')}")
        print(f"   Category: {source.get('source_category')}")

    print("=" * 60)
