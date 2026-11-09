from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db, engine
from sqlalchemy import text
from app.init_db import init_db
from app.search import fetch_claim_evidence
from app.nlp_processor import filter_relevant_evidence
from app.rag_engine import (
    analyze_claim_with_llm,
    check_gemini_health,
)
from app.crud import save_verification_result
from app.models import ClaimRecord

# Initialize database when the application starts.
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Real-Time AI News Verification System",
    description="Verify news claims using live web evidence and AI analysis.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ClaimRequest(BaseModel):
    claim: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="The news claim to verify",
    )

@app.get("/")
def home():
    return {
        "message": "Real-Time AI News Verification API is running",
        "docs": "/docs",
    }

@app.get("/health")
def health():
    database_status = "operational"
    gemini_status = "operational"

    # Database health check
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        database_status = "unavailable"

    # Gemini health check
    gemini_status = check_gemini_health()

    return {
        "status": "healthy",
        "database": database_status,
        "gemini": gemini_status,
    }

@app.post("/verify")
def verify_claim(
    request: ClaimRequest,
    db: Session = Depends(get_db),
):
    claim = request.claim.strip()

    if not claim:
        raise HTTPException(
            status_code=400,
            detail="Claim cannot be empty."
        )

    try:
        # 1. Retrieve live search results.
        articles = fetch_claim_evidence(
            claim,
            max_results=5
        )

        # 2. Extract relevant evidence using NLP.
        evidence = filter_relevant_evidence(
            claim,
            articles,
            threshold=0.50,
            top_k=5,
        )

        # 3. Analyze evidence using Gemini.
        if not evidence:
            report = {
                "verdict": "UNVERIFIED",
                "confidence_score": 0,
                "explanation": (
                    "We could not find sufficient relevant evidence to "
                    "confirm or contradict this claim. This does not mean "
                    "the claim is false; the available evidence is "
                    "inconclusive."
                ),
                "past_events": [],
                "current_and_future_updates": [],
                "sources": [],
                "evidence_analysis": [],
                "evidence_status": "INSUFFICIENT_EVIDENCE",
                "recommended_action": (
                    "Check reliable primary sources or try again later."
                ),
            }

        else:
            report = analyze_claim_with_llm(
                claim,
                evidence
            )

        # 4. Save the verification result.
        saved_claim = save_verification_result(
            db,
            claim,
            report
        )

        # 5. Retrieve evidence analysis.
        evidence_analysis = report.get(
            "evidence_analysis",
            []
        )

        if not isinstance(evidence_analysis, list):
            evidence_analysis = []

        # 6. Count each evidence classification.
        stance_counts = {
            "SUPPORTING": 0,
            "CONTRADICTING": 0,
            "CONTEXTUAL": 0
        }

        for item in evidence_analysis:
            if not isinstance(item, dict):
                continue

            stance = item.get("stance")

            if stance in stance_counts:
                stance_counts[stance] += 1

        # 7. Determine evidence status.
        evidence_status = report.get(
            "evidence_status",
            "EVIDENCE_FOUND" if evidence else "INSUFFICIENT_EVIDENCE"
        )

        # 8. Return the complete verification report.
        return {
            "claim_id": saved_claim.id,
            "claim": claim,
            "verdict": report.get("verdict", "UNVERIFIED"),
            "confidence_score": report.get("confidence_score", 0),
            "explanation": report.get("explanation", ""),
            "past_events": report.get("past_events", []),
            "current_and_future_updates": report.get(
                "current_and_future_updates",
                []
            ),

            # Source metadata.
            "sources": report.get("sources", []),

            # Original evidence sentences.
            "evidence_count": len(evidence),
            "evidence": evidence,

            # Individual evidence classifications.
            "evidence_analysis": evidence_analysis,

            # Evidence classification counts.
            "supporting_evidence_count": stance_counts["SUPPORTING"],
            "contradicting_evidence_count": stance_counts["CONTRADICTING"],
            "contextual_evidence_count": stance_counts["CONTEXTUAL"],

            # Additional verification information.
            "evidence_status": evidence_status,
            "recommended_action": report.get(
                "recommended_action",
                None
            ),
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
        .all()
    )

    return [
        {
            "claim_id": record.id,
            "claim": record.claim_text,
            "verdict": record.verdict,
            "confidence_score": record.confidence_score,
            "explanation": record.explanation,
            "created_at": (
                record.created_at.isoformat()
                if record.created_at else None
            ),
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
