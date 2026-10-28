from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.init_db import init_db
from app.search import fetch_live_news_evidence
from app.nlp_processor import filter_relevant_evidence
from app.rag_engine import analyze_claim_with_llm
from app.crud import save_verification_result
from app.models import ClaimRecord

app = FastAPI(
    title="Real-Time AI News Verification System",
    description="Verify news claims using live web evidence and AI analysis.",
    version="1.0.0",
)


class ClaimRequest(BaseModel):
    claim: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="The news claim to verify",
    )


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def home():
    return {
        "message": "Real-Time AI News Verification API is running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/verify")
def verify_claim(
    request: ClaimRequest,
    db: Session = Depends(get_db),
):
    claim = request.claim.strip()

    if not claim:
        raise HTTPException(status_code=400, detail="Claim cannot be empty.")

    try:
        # 1. Retrieve live search results
        articles = fetch_live_news_evidence(claim, max_results=5)

        # 2. Select relevant evidence
        evidence = filter_relevant_evidence(
            claim,
            articles,
            threshold=0.50,
            top_k=5,
        )
        if not evidence:
            report = {
                "verdict": "UNVERIFIED",
                "confidence_score": 0,
                "explanation": (
                    "We could not find sufficient relevant evidence to confirm "
                    "or contradict this claim. This does not mean the claim is "
                    "false; the available evidence is inconclusive."
                ),
                "past_events": [],
                "current_and_future_updates": [],
                "sources": [],
                "evidence_status": "INSUFFICIENT_EVIDENCE",
                "recommended_action": (
                    "Check reliable primary sources or try again later."
                ),
            }
        else:
            report = analyze_claim_with_llm(claim, evidence)
        
        # 4. Save the claim, verdict, and source links
        saved_claim = save_verification_result(db, claim, report)

        # 5. Return the complete verification report
        return {
            "claim_id": saved_claim.id,
            "claim": claim,
            "verdict": report.get("verdict", "UNVERIFIED"),
            "confidence_score": report.get("confidence_score", 0),
            "explanation": report.get("explanation", ""),
            "past_events": report.get("past_events", []),
            "current_and_future_updates": report.get(
                "current_and_future_updates", []
            ),
            "sources": report.get("sources", []),
            "evidence_count": len(evidence),
            "evidence": evidence,
        }

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {type(exc).__name__}: {exc}",
        ) from exc

@app.get("/history")
def get_verification_history(
    db: Session = Depends(get_db),
):
    records = (
        db.query(ClaimRecord)
        .order_by(ClaimRecord.created_at.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "claim_id": record.id,
            "claim": record.claim_text,
            "verdict": record.verdict,
            "confidence_score": record.confidence_score,
            "explanation": record.explanation,
            "created_at": record.created_at.isoformat()
            if record.created_at else None,
            "sources": [
                {
                    "title": source.title,
                    "url": source.url,
                }
                for source in record.sources
            ],
        }
        for record in records
    ]
