from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional


# =========================
# USER SCHEMAS
# =========================

class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# =========================
# AI RESPONSE STRUCTURE
# =========================

class VerseResponse(BaseModel):
    chapter: Optional[int] = None
    verse_number: Optional[int] = None
    sanskrit: Optional[str] = None
    meaning: Optional[str] = None
    explanation: str


# =========================
# MESSAGE SCHEMAS
# =========================

class MessageCreate(BaseModel):
    text: str = Field(..., min_length=1)
    voice_mode: Optional[bool] = False


class MessageResponse(BaseModel):
    sender: str
    text: VerseResponse
    emotion: Optional[str] = None
    timestamp: datetime
    audio_url: Optional[str] = None

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    messages: List[MessageResponse]


# =========================
# JWT TOKEN SCHEMAS
# =========================

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


# =========================
# WELLNESS SCHEMAS
# =========================

class WellnessAssessmentCreate(BaseModel):
    test_type: str
    score: int
    level: str


class WellnessAssessmentResponse(BaseModel):
    id: int
    test_type: str
    score: int
    level: str
    taken_at: datetime

    class Config:
        from_attributes = True


# =========================
# ABHYASA SCHEMAS
# =========================

class AbhyasaLogCreate(BaseModel):
    minutes: int


class AbhyasaLogResponse(BaseModel):
    id: int
    meditation_minutes: int
    streak_count: int
    logged_date: datetime

    class Config:
        from_attributes = True


class AbhyasaStatsResponse(BaseModel):
    meditation: int
    streak: int