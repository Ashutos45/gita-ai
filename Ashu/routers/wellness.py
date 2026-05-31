# Ashu/routers/wellness.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from Ashu.database import SessionLocal
from Ashu.models import WellnessAssessment, User
from Ashu.schemas import WellnessAssessmentCreate, WellnessAssessmentResponse
from Ashu.auth import get_current_user

router = APIRouter(prefix="/wellness", tags=["wellness"])


# =====================================
# Database Dependency
# =====================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================
# SUBMIT ASSESSMENT
# =====================================

@router.post("/assessment", response_model=WellnessAssessmentResponse)
def submit_assessment(
    assessment: WellnessAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_assessment = WellnessAssessment(
        user_id=current_user.id,
        test_type=assessment.test_type,
        score=assessment.score,
        level=assessment.level
    )
    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)
    return new_assessment


# =====================================
# GET ASSESSMENT HISTORY
# =====================================

@router.get("/history", response_model=List[WellnessAssessmentResponse])
def get_assessment_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = db.query(WellnessAssessment).filter(
        WellnessAssessment.user_id == current_user.id
    ).order_by(WellnessAssessment.taken_at.desc()).all()
    return history
