from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class ClaimRecord(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_text = Column(Text, nullable=False)
    verdict = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sources = relationship("SourceRecord", back_populates="claim", cascade="all, delete-orphan")


class SourceRecord(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    title = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)

    claim = relationship("ClaimRecord", back_populates="sources")