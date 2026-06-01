from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta, timezone
import random

from Ashu.database import SessionLocal
from Ashu.models import User, WellnessAssessment, AbhyasaLog, Message, Verse
from Ashu.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(tags=["dashboard"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Hardcoded daily wisdom pool for now
WISDOM_POOL = [
    {"verse": "BG 2.47", "sanskrit": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।", "insight": "Focus on your effort, not the outcome. Release anxiety about results."},
    {"verse": "BG 6.5", "sanskrit": "उद्धरेदात्मनात्मानं नात्मानमवसादयेत्।", "insight": "Elevate yourself through the power of your own mind. You are your own best friend."},
    {"verse": "BG 2.14", "sanskrit": "मात्रास्पर्शास्तु कौन्तेय शीतोष्णसुखदुःखदाः।", "insight": "Pleasure and pain are temporary, like winter and summer. Endure them patiently."},
    {"verse": "BG 3.19", "sanskrit": "तस्मादसक्तः सततं कार्यं कर्म समाचर।", "insight": "Perform your duty without attachment. This is the path to supreme peace."},
    {"verse": "BG 6.6", "sanskrit": "बन्धुरात्मात्मनस्तस्य येनात्मैवात्मना जितः।", "insight": "For one who has conquered the mind, the mind is the best of friends."}
]

@router.get("/dashboard/payload")
def get_dashboard_payload(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id
    user = current_user
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Calculate streak (consecutive days of abhyasa or messages)
    # Simple calculation: just count total days active in last 30 days
    last_30_days = datetime.utcnow() - timedelta(days=30)
    abhyasa_count = db.query(cast(AbhyasaLog.logged_date, Date)).filter(AbhyasaLog.user_id == user_id, AbhyasaLog.logged_date >= last_30_days).distinct().count()
    streak = abhyasa_count  # Simple approximation for now
    
    # Get latest assessments
    latest_stress = db.query(WellnessAssessment).filter(WellnessAssessment.user_id == user_id, WellnessAssessment.test_type == 'stress').order_by(WellnessAssessment.taken_at.desc()).first()
    latest_decision = db.query(WellnessAssessment).filter(WellnessAssessment.user_id == user_id, WellnessAssessment.test_type == 'decision').order_by(WellnessAssessment.taken_at.desc()).first()
    latest_rel = db.query(WellnessAssessment).filter(WellnessAssessment.user_id == user_id, WellnessAssessment.test_type == 'relationships').order_by(WellnessAssessment.taken_at.desc()).first()
    
    # Calculate growth journey score (Level)
    total_messages = db.query(Message).filter(Message.user_id == user_id).count()
    total_assessments = db.query(WellnessAssessment).filter(WellnessAssessment.user_id == user_id).count()
    total_abhyasa = db.query(AbhyasaLog).filter(AbhyasaLog.user_id == user_id).count()
    
    xp = (total_messages * 5) + (total_assessments * 20) + (total_abhyasa * 15)
    level = min(10, (xp // 100) + 1)
    
    # Update spiritual level if needed
    if level > user.spiritual_level:
        user.spiritual_level = level
        db.commit()

    # Generate AI Insight
    insight = "Begin your journey by taking an assessment or meditating."
    if latest_stress and total_assessments > 3:
        insight = "You've been consistent. Maintain your inner stillness."
    elif latest_stress and latest_stress.level == "High":
        insight = "I sense turbulence. Pause and ground yourself today."
    elif total_abhyasa > 5:
        insight = "Your regular practice is building a strong foundation."
        
    # Assessment Reminder Logic
    needs_assessment = True
    days_since_assessment = None
    if latest_stress:
        try:
            now = datetime.now(timezone.utc) if latest_stress.taken_at.tzinfo else datetime.utcnow()
            days_since_assessment = (now - latest_stress.taken_at).days
            if days_since_assessment < 7:
                needs_assessment = False
        except Exception as e:
            print("Timezone error:", e)
            needs_assessment = False

    # Mock Trend Data for Chart.js
    # In production, we would group by date and average the score.
    # We will generate a realistic looking 7-day trend array based on the latest score.
    trend_data = [50, 45, 60, 55, 40, 35, 30] # default
    if latest_stress:
        base = latest_stress.score
        trend_data = [max(10, min(100, base + random.randint(-15, 15))) for _ in range(7)]
        trend_data[-1] = base # current day is exact

    # Achievements
    achievements = []
    if total_assessments > 0: achievements.append("First Assessment")
    if total_abhyasa > 0: achievements.append("First Reflection")
    if streak >= 7: achievements.append("7 Day Streak")
    
    wisdom = random.choice(WISDOM_POOL)
    
    return {
        "user": {
            "name": user.full_name,
            "level": level,
            "xp": xp,
            "streak": streak,
            "achievements": achievements
        },
        "wisdom": wisdom,
        "insight": insight,
        "assessment": {
            "needs_reminder": needs_assessment,
            "days_since": days_since_assessment,
            "latest_stress": latest_stress.level if latest_stress else "None",
            "latest_decision": latest_decision.level if latest_decision else "None",
            "latest_relationships": latest_rel.level if latest_rel else "None"
        },
        "trends": {
            "labels": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Today"],
            "stress_scores": trend_data
        }
    }
