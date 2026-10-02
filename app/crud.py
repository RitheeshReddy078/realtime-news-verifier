from sqlalchemy.orm import Session
from app.models import ClaimRecord, SourceRecord

def save_verification_result(db: Session, claim_text: str, report: dict):
    # 1. Create main claim record
    db_claim = ClaimRecord(
        claim_text=claim_text,
        verdict=report.get("verdict", "UNVERIFIED"),
        confidence_score=report.get("confidence_score", 0.0),
        explanation=report.get("explanation", "No explanation provided.")
    )
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)

    # 2. Save sources linked to this claim
    sources = report.get("sources", [])
    for src in sources:
        db_source = SourceRecord(
            claim_id=db_claim.id,
            title=src.get("title", "Unknown Title"),
            url=src.get("url", "#")
        )
        db.add(db_source)
    
    db.commit()
    return db_claim