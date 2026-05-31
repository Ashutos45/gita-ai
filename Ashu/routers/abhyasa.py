# Ashu/routers/abhyasa.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from Ashu.database import SessionLocal
from Ashu.models import AbhyasaLog, User
from Ashu.schemas import AbhyasaLogCreate, AbhyasaLogResponse, AbhyasaStatsResponse
from Ashu.auth import get_current_user

router = APIRouter(prefix="/abhyasa", tags=["abhyasa"])


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
# LOG MEDITATION SESSION
# =====================================

@router.post("/log", response_model=AbhyasaLogResponse)
def log_meditation(
    log: AbhyasaLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Retrieve user's last meditation session
    last_log = db.query(AbhyasaLog).filter(
        AbhyasaLog.user_id == current_user.id
    ).order_by(AbhyasaLog.logged_date.desc()).first()

    today = datetime.utcnow().date()
    streak = 1

    if last_log:
        last_date = last_log.logged_date.date()
        
        if last_date == today:
            # Already meditated today: maintain current streak
            streak = last_log.streak_count
        elif last_date == today - timedelta(days=1):
            # Meditated yesterday: continue streak
            streak = last_log.streak_count + 1
        else:
            # Streak broken: reset to 1
            streak = 1

    new_log = AbhyasaLog(
        user_id=current_user.id,
        meditation_minutes=log.minutes,
        streak_count=streak
    )
    
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    
    return new_log


# =====================================
# GET CURRENT STATS (TODAY'S MINS & STREAK)
# =====================================

@router.get("/stats", response_model=AbhyasaStatsResponse)
def get_meditation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get last log to check the current streak
    last_log = db.query(AbhyasaLog).filter(
        AbhyasaLog.user_id == current_user.id
    ).order_by(AbhyasaLog.logged_date.desc()).first()

    today = datetime.utcnow().date()
    streak = 0
    meditation_today = 0

    if last_log:
        last_date = last_log.logged_date.date()
        
        # If last logged was today or yesterday, streak is active
        if last_date == today or last_date == today - timedelta(days=1):
            streak = last_log.streak_count
        else:
            # Streak has expired/broken
            streak = 0

        # Calculate sum of meditation minutes for today
        today_start = datetime(today.year, today.month, today.day)
        logs_today = db.query(AbhyasaLog).filter(
            AbhyasaLog.user_id == current_user.id,
            AbhyasaLog.logged_date >= today_start
        ).all()
        
        meditation_today = sum(l.meditation_minutes for l in logs_today)

    return {
        "meditation": meditation_today,
        "streak": streak
    }
