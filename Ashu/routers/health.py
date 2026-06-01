from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any

from Ashu.database import SessionLocal
from Ashu.models import User
from Ashu.auth import get_current_user

router = APIRouter(tags=["health"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/health/dashboard")
def health_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    status = {
        "postgres_read": "FAIL",
        "auth_token": "PASS", # Depends(get_current_user) succeeded
        "wellness_api": "PASS",
        "abhyasa_api": "PASS",
        "overall_status": "PASS",
        "failing_endpoint": None
    }
    
    try:
        # Test 1: PostgreSQL Read
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            status["postgres_read"] = "PASS"
        else:
            raise Exception("PostgreSQL returned unexpected value")
            
        # Test 2: Wellness API dependencies (check table access)
        from Ashu.models import WellnessAssessment
        db.query(WellnessAssessment).first()
        
        # Test 3: Abhyasa API dependencies (check table access)
        from Ashu.models import AbhyasaLog
        db.query(AbhyasaLog).first()
        
    except Exception as e:
        status["overall_status"] = "FAIL"
        
        if status["postgres_read"] == "FAIL":
            status["failing_endpoint"] = "Database Connection"
        else:
            # We can deduce based on where it failed if we wrapped each closely, 
            # but for simplicity, we catch it broadly here and mark the first presumed failure.
            # Let's just output the exact exception as the failing endpoint reason for deep debugging.
            status["failing_endpoint"] = f"API Dependency Error: {str(e)}"
            status["wellness_api"] = "FAIL"
            status["abhyasa_api"] = "FAIL"

    return status

@router.get("/health/database")
def health_database(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "Database connection successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/health/models")
def health_models(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import inspect
        from Ashu.database import engine
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        table_columns = {}
        for table in tables:
            columns = [col["name"] for col in inspector.get_columns(table)]
            table_columns[table] = columns
            
        return {"status": "ok", "tables": table_columns}
    except Exception as e:
        return {"status": "error", "message": str(e)}
