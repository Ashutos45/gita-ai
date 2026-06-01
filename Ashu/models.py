from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Float,
    UniqueConstraint,
    Index,
    Boolean
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from Ashu.database import Base


# ==========================
# User Model
# ==========================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    # 🔥 Future AI growth tracking
    spiritual_level = Column(Integer, nullable=False, default=1)
    addiction_score = Column(Float, nullable=False, default=0.0)

    # Preferred UI / interaction language
    preferred_language = Column(String(10), nullable=False, default="en")

    # Dynamic running psychological profile summary
    memory_summary = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    messages = relationship(
        "Message",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    wellness_assessments = relationship(
        "WellnessAssessment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    abhyasa_logs = relationship(
        "AbhyasaLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    daily_checkins = relationship(
        "DailyCheckin",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    favorite_verses = relationship(
        "FavoriteVerse",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# ==========================
# Message Model
# ==========================

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    sender = Column(String(10), nullable=False, index=True)  # "user" or "ai"
    text = Column(Text, nullable=False)

    # 🔥 Emotion tracking
    emotion = Column(String(50), nullable=True, index=True)
    emotion_intensity = Column(Float, nullable=False, default=0.5)

    # 🔥 Associated verse context
    chapter = Column(Integer, nullable=True, index=True)
    verse_number = Column(Integer, nullable=True, index=True)
    verse_id = Column(
        Integer,
        ForeignKey("verses.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="messages")
    verse = relationship("Verse")

    __table_args__ = (
        Index("idx_user_timestamp", "user_id", "timestamp"),
    )


# ==========================
# Emotion Model
# ==========================

class Emotion(Base):
    __tablename__ = "emotions"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(50), unique=True, nullable=False, index=True)

    emotion_links = relationship(
        "EmotionVerseMap",
        back_populates="emotion",
        cascade="all, delete-orphan"
    )


# ==========================
# Verse Model
# ==========================

class Verse(Base):
    __tablename__ = "verses"

    id = Column(Integer, primary_key=True, index=True)

    chapter = Column(Integer, nullable=False, index=True)
    verse_number = Column(Integer, nullable=False, index=True)

    sanskrit = Column(Text, nullable=False)
    transliteration = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("chapter", "verse_number", name="unique_chapter_verse"),
        Index("idx_chapter_verse", "chapter", "verse_number"),
    )

    translations = relationship(
        "VerseTranslation",
        back_populates="verse",
        cascade="all, delete-orphan"
    )

    emotion_links = relationship(
        "EmotionVerseMap",
        back_populates="verse",
        cascade="all, delete-orphan"
    )


# ==========================
# Verse Translation Model
# ==========================

class VerseTranslation(Base):
    __tablename__ = "verse_translations"

    id = Column(Integer, primary_key=True, index=True)

    verse_id = Column(
        Integer,
        ForeignKey("verses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    language = Column(String(10), nullable=False, index=True)  # en, hi, ta
    meaning = Column(Text, nullable=False)

    verse = relationship("Verse", back_populates="translations")

    __table_args__ = (
        Index("idx_verse_language", "verse_id", "language"),
    )


# ==========================
# Emotion ↔ Verse Mapping
# ==========================

class EmotionVerseMap(Base):
    __tablename__ = "emotion_verse_map"

    id = Column(Integer, primary_key=True, index=True)

    emotion_id = Column(
        Integer,
        ForeignKey("emotions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    verse_id = Column(
        Integer,
        ForeignKey("verses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 🔥 Smarter verse selection
    weight = Column(Float, nullable=False, default=1.0)
    priority = Column(Integer, nullable=False, default=1)

    # 🔥 AI learning signals
    usage_count = Column(Integer, nullable=False, default=0)
    effectiveness_score = Column(Float, nullable=False, default=0.0)

    emotion = relationship("Emotion", back_populates="emotion_links")
    verse = relationship("Verse", back_populates="emotion_links")

    __table_args__ = (
        UniqueConstraint("emotion_id", "verse_id", name="unique_emotion_verse"),
        Index("idx_emotion_verse", "emotion_id", "verse_id"),
    )


# ==========================
# Wellness Assessment Model
# ==========================

class WellnessAssessment(Base):
    __tablename__ = "wellness_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    test_type = Column(String(50), nullable=False, index=True)  # "stress", "decision", "relationships"
    score = Column(Integer, nullable=False)
    level = Column(String(20), nullable=False, index=True)  # "Low", "Moderate", "High"
    taken_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="wellness_assessments")


# ==========================
# Abhyasa Log Model (Meditation Tracker)
# ==========================

class AbhyasaLog(Base):
    __tablename__ = "abhyasa_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    meditation_minutes = Column(Integer, nullable=False)
    read_gita = Column(Boolean, nullable=False, default=False)
    reflection_done = Column(Boolean, nullable=False, default=False)
    self_control_practiced = Column(Boolean, nullable=False, default=False)
    streak_count = Column(Integer, nullable=False, default=0)
    logged_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="abhyasa_logs")


# ==========================
# Daily Checkin Model (Mood Tracker)
# ==========================

class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    mood = Column(String(50), nullable=False)  # Happy, Calm, Anxious, Sad, Frustrated
    notes = Column(Text, nullable=True)
    logged_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="daily_checkins")


# ==========================
# Favorite Verse Model
# ==========================

class FavoriteVerse(Base):
    __tablename__ = "favorite_verses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    verse_id = Column(String(50), nullable=False) # e.g. "BG 2.47"
    sanskrit = Column(Text, nullable=True)
    translation = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    saved_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="favorite_verses")