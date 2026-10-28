import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")

def analyze_claim_with_llm(claim: str, evidence_list: list[dict]) -> dict:
    """
    Analyzes claim against evidence using Gemini LLM with dynamic date grounding and timeline extraction.
    """
    if not LLM_API_KEY or LLM_API_KEY == "your_actual_openai_or_gemini_api_key_here":
        return {
            "verdict": "UNVERIFIED",
            "confidence_score": 0,
            "explanation": "LLM API Key missing in .env file.",
            "past_events": [],
            "current_and_future_updates": [],
            "sources": []
        }

    
    if not evidence_list:
        return {
            "verdict": "UNVERIFIED",
            "confidence_score": 0,
            "explanation": (
                "We could not find sufficient relevant evidence to confirm "
                "or contradict this claim. This does not mean the claim is "
                "false; it means the available evidence is inconclusive. "
                "Check reliable primary sources or try again later."
            ),
            "past_events": [],
            "current_and_future_updates": [],
            "sources": [],
            "evidence_status": "INSUFFICIENT_EVIDENCE",
            "recommended_action": (
                "Seek confirmation from reliable primary sources, "
                "such as official organizations or original research."
            )
        }


    # Dynamic current date string
    today_str = datetime.now().strftime("%B %d, %Y")

    # Format evidence into prompt
    formatted_evidence = ""
    sources = []
    for idx, item in enumerate(evidence_list, 1):
        formatted_evidence += f"Evidence {idx}: \"{item['evidence_sentence']}\" (Source: {item['source_title']})\n"
        sources.append({"title": item["source_title"], "url": item["source_url"]})

    prompt = f"""
You are an expert AI Time-Aware News Verification System.
TODAY'S DATE IS: {today_str}

USER CLAIM: "{claim}"

RETRIEVED EVIDENCE:
{formatted_evidence}


INSTRUCTIONS:
1. Evaluate whether each evidence snippet directly addresses the specific USER CLAIM, not merely the same general topic.
2. Return SUPPORTED only when reliable evidence directly supports the claim.
3. Return CONTRADICTED only when reliable evidence directly contradicts the claim.
4. Return MISLEADING when the claim substantially misrepresents evidence or omits important context.
5. Return UNVERIFIED when evidence is missing, indirect, weak, unrelated, or inconclusive.
6. Do not treat the absence of evidence as proof that the claim is false.
7. Do not invent events, dates, announcements, or future updates. Include them only when directly supported by retrieved evidence.
8. If evidence is insufficient or unrelated, use a low confidence score (0–20), explain what could not be established, and leave past_events and current_and_future_updates empty.
9. Confidence must reflect the strength and relevance of the evidence, not merely how certain the answer sounds.
10. Output MUST be valid JSON strictly matching this schema:

{{
  "verdict": "SUPPORTED|CONTRADICTED|MISLEADING|UNVERIFIED",
  "confidence_score": 90,
  "explanation": "A concise 2-sentence summary grounded strictly on the evidence.",
  "past_events": [
    {{
      "event": "Description of past action",
      "date": "Exact or approximate date",
      "relative_time": "e.g., 5 days ago / earlier in 2026"
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

    # Priority list of model names to try sequentially if one is unavailable or rate-limited
    candidate_models = [
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash"
    ]

    client = genai.Client(api_key=LLM_API_KEY)
    last_error = None

    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            parsed_result = json.loads(response.text)
            parsed_result["sources"] = sources
            return parsed_result

        except Exception as e:
            last_error = e
            # Small backoff before testing next model candidate
            time.sleep(1)
            continue

    print(f"Error calling LLM after trying fallback models: {last_error}")
    return {
        "verdict": "UNVERIFIED",
        "confidence_score": 0,
        "explanation": f"Failed to perform LLM analysis: {str(last_error)}",
        "past_events": [],
        "current_and_future_updates": [],
        "sources": sources
    }

if __name__ == "__main__":
    from app.search import fetch_live_news_evidence
    from app.nlp_processor import filter_relevant_evidence

    test_claim = "ISRO space mission launches"
    print(f"Running Time-Aware Verification for claim: '{test_claim}'...\n")

    articles = fetch_live_news_evidence(test_claim, max_results=3)
    evidence = filter_relevant_evidence(test_claim, articles, threshold=0.30, top_k=3)
    report = analyze_claim_with_llm(test_claim, evidence)

    print("=" * 60)
    print("              TIME-AWARE VERIFICATION REPORT           ")
    print("=" * 60)
    print(f"VERDICT         : {report.get('verdict')}")
    print(f"CONFIDENCE      : {report.get('confidence_score')}%")
    print(f"\nEXPLANATION:\n{report.get('explanation')}\n")

    print("-" * 60)
    print("PAST VERIFIED EVENTS:")
    for item in report.get("past_events", []):
        print(f" • {item.get('event')}")
        print(f"   Date: {item.get('date')} ({item.get('relative_time')})\n")

    print("-" * 60)
    print("CURRENT & UPCOMING UPDATES:")
    for item in report.get("current_and_future_updates", []):
        print(f" • {item.get('update')}")
        print(f"   Timeframe: {item.get('expected_timeframe')}\n")

    print("-" * 60)
    print("VERIFIED SOURCES:")
    for src in report.get("sources", []):
        print(f" • {src.get('title')}: {src.get('url')}")
    print("=" * 60)