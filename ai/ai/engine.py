# ======================================
# IMPORTS
# ======================================

import os
import html
from pydantic import BaseModel, Field
from typing import List

from ai.ai.pipeline import gita_pipeline
from ai.ai.response_builder import build_response
from ai.ai.memory_engine import get_user_memory

from Ashu.database import SessionLocal
from Ashu.models import Emotion, EmotionVerseMap, Verse, Message, User, VerseTranslation

from sqlalchemy.exc import SQLAlchemyError


# ======================================
# Pydantic schemas for Gemini Structured Output
# ======================================

class SeekerGuidance(BaseModel):
    emotional_understanding: str = Field(description="A compassionate, brief acknowledgment of the seeker's current emotional state.")
    why_chosen: str = Field(description="Explanation of why the selected verse is relevant to the seeker's context.")
    personalized_guidance: str = Field(description="Philosophical, Krishna-inspired counseling tailored to the user's specific struggle and memory context.")
    practical_steps: List[str] = Field(description="2 or 3 clear, actionable steps the seeker can take today.")
    reflection_exercise: str = Field(description="A question or exercise for self-reflection.")


class QueryAnalysis(BaseModel):
    lang: str = Field(description="2-character language ISO code (en, hi, sa, ta, te, or)")
    translated_query: str = Field(description="The user query translated into English. If the query is already in English, return it unchanged.")


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        print("[Gemini Client] Failed to initialize:", e)
        return None


def get_verse_translation_with_fallback(db, verse_id: int, target_lang: str) -> str:
    # 1. Database Translation Priority
    v_trans = db.query(VerseTranslation).filter(
        VerseTranslation.verse_id == verse_id,
        VerseTranslation.language == target_lang
    ).first()
    if v_trans:
        return v_trans.meaning
        
    # Get English translation for fallbacks
    en_trans = db.query(VerseTranslation).filter(
        VerseTranslation.verse_id == verse_id,
        VerseTranslation.language == "en"
    ).first()
    en_meaning = en_trans.meaning if en_trans else ""
    
    if not en_meaning:
        any_trans = db.query(VerseTranslation).filter(
            VerseTranslation.verse_id == verse_id
        ).first()
        en_meaning = any_trans.meaning if any_trans else "Translation unavailable."
        
    if target_lang == "en":
        return en_meaning

    # 2. Gemini Translation Fallback
    client = get_gemini_client()
    if client and en_meaning:
        try:
            translation_instruction = (
                f"Translate the following Bhagavad Gita verse translation into the target language: {target_lang}. "
                "Maintain the sacred, scriptural, and poetic tone of the teachings."
            )
            from google.genai import types
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Verse English translation: '{en_meaning}'",
                config=types.GenerateContentConfig(
                    system_instruction=translation_instruction,
                    temperature=0.3,
                    http_options=types.HttpOptions(timeout=4.0)
                )
            )
            translated_text = response.text.strip() if response.text else ""
            if translated_text:
                print(f"[Translation Pipeline] Translated Verse ID {verse_id} to {target_lang} dynamically.")
                return translated_text
        except Exception as e:
            print(f"[Translation Pipeline] Gemini translation to {target_lang} failed:", e)
            
    # 3. English Translation Fallback
    return en_meaning


def regenerate_user_memory_summary(db, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
        
    # Fetch last 10 messages of the user chronologically
    past_messages = (
        db.query(Message)
        .filter(Message.user_id == user_id)
        .order_by(Message.timestamp.desc())
        .limit(10)
        .all()
    )
    past_messages.reverse()
    
    history_text = "\n".join(
        f"{'Seeker' if msg.sender == 'user' else 'Krishna'}: {msg.text}"
        for msg in past_messages
    )
    
    client = get_gemini_client()
    if client and history_text:
        try:
            summarization_instruction = (
                "Analyze the user query history with Krishna. "
                "Regenerate a new, unified Seeker psychological profile in exactly 3 to 5 concise sentences. "
                "Focus ONLY on high-level patterns: their current primary emotional struggle, "
                "their general receptiveness to guidance, and any ongoing concerns (like exams, career, or self-control). "
                "Do NOT append to the previous summary; construct it completely fresh. "
                "Do NOT quote raw conversation lines. "
                "Do NOT include highly sensitive, specific personal identifiers or private details."
            )
            from google.genai import types
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Conversation History:\n{history_text}",
                config=types.GenerateContentConfig(
                    system_instruction=summarization_instruction,
                    temperature=0.5,
                    http_options=types.HttpOptions(timeout=5.0)
                )
            )
            summary_text = response.text.strip() if response.text else ""
            if summary_text:
                user.memory_summary = summary_text
                db.commit()
                print(f"[Memory Engine] Regenerated profile summary for user {user_id}: {summary_text}")
        except Exception as e:
            print(f"[Memory Engine] Failed to summarize profile for user {user_id}: {e}")


def format_krishna_response_to_html(guidance, verse, target_lang="en") -> str:
    # 1. Sanitize all generated inputs to prevent HTML/Script Injection (XSS protection)
    emotional_understanding = html.escape(guidance.emotional_understanding)
    why_chosen = html.escape(guidance.why_chosen)
    personalized_guidance = html.escape(guidance.personalized_guidance)
    reflection_exercise = html.escape(guidance.reflection_exercise)
    
    # 2. Sanitize list items
    steps_list = "".join(
        f"<li style='margin-bottom: 4px;'>{html.escape(step)}</li>"
        for step in guidance.practical_steps
    )
    
    # 3. Ground the verse properties from the local database strictly (unhallucinated)
    chapter = verse.get("chapter") if verse else None
    verse_number = verse.get("verse_number") if verse else None
    sanskrit = verse.get("sanskrit") if verse else None
    translation = verse.get("meaning") if verse else None
    
    verse_citation_html = ""
    if chapter and verse_number:
        verse_citation_html = f"""
        <div class="verse-citation" style="font-weight: bold; color: #b45309; margin-bottom: 6px;">
          Relevant Verse: Bhagavad Gita • Chapter {chapter}, Verse {verse_number}
        </div>
        """
        
    sanskrit_html = ""
    if sanskrit:
        sanskrit_html = f"""
        <div class="sanskrit-text" style="font-family: 'Noto Serif Devanagari', serif; font-size: 1.15em; line-height: 1.6; color: #1e293b; background: #fffbeb; padding: 10px; border-radius: 8px; border-left: 4px solid #f59e0b; margin-bottom: 8px; font-style: normal;">
          {html.escape(sanskrit)}
        </div>
        """
        
    translation_html = ""
    if translation:
         translation_html = f"""
         <div class="translation-text" style="font-size: 0.95em; color: #4b5563; margin-bottom: 12px; font-style: italic;">
           <strong>Translation:</strong> {html.escape(translation)}
         </div>
         """

    html_content = f"""<div class="krishna-response" style="font-family: 'Crimson Text', serif; color: #3b2510; line-height: 1.6; display: flex; flex-direction: column; gap: 12px;">
  
  <!-- 1. Emotional Understanding -->
  <div class="understanding-block" style="font-style: italic; border-left: 3px solid #facc15; padding-left: 12px; margin-bottom: 8px;">
    {emotional_understanding}
  </div>

  <!-- 2, 3, 4: Grounded Verse Data (Sanitized & Strict) -->
  {verse_citation_html}
  {sanskrit_html}
  {translation_html}

  <!-- 5. Why This Verse Was Chosen -->
  <div class="verse-choice" style="font-size: 0.95em; color: #78350f; background: rgba(251, 191, 36, 0.08); padding: 10px; border-radius: 8px;">
    <strong>Why this wisdom was chosen:</strong> {why_chosen}
  </div>

  <!-- 6. Personalized Guidance -->
  <div class="guidance-block" style="font-size: 1.05em; line-height: 1.7; margin-bottom: 8px;">
    {personalized_guidance}
  </div>

  <!-- 7. Practical Steps -->
  <div class="practical-block" style="background: rgba(254, 243, 199, 0.5); padding: 14px; border-radius: 12px; border: 1px solid rgba(250, 204, 21, 0.25);">
    <strong style="color: #b45309; display: block; margin-bottom: 6px;">👣 Actions for Alignment:</strong>
    <ul style="margin: 0; padding-left: 18px; display: flex; flex-direction: column; gap: 4px;">
       {steps_list}
    </ul>
  </div>

  <!-- 8. Reflection Exercise -->
  <div class="reflection-block" style="border-top: 1px dashed rgba(250, 204, 21, 0.4); padding-top: 10px; margin-top: 8px; font-size: 0.95em; color: #4b5563;">
    <strong style="color: #d97706;">🧘 Reflection:</strong> {reflection_exercise}
  </div>
</div>"""
    return html_content


# ======================================
# Fallback Emotion-Based Verse Selector
# ======================================

def get_emotion_fallback_verse(emotion_name: str):

    if not emotion_name:
        return None

    db = SessionLocal()

    try:
        emotion = db.query(Emotion).filter(
            Emotion.name == emotion_name
        ).first()

        if not emotion:
            return None

        mapping = (
            db.query(EmotionVerseMap)
            .filter(EmotionVerseMap.emotion_id == emotion.id)
            .order_by(EmotionVerseMap.weight.desc())
            .first()
        )

        if not mapping:
            return None

        verse = db.query(Verse).filter(
            Verse.id == mapping.verse_id
        ).first()

        if not verse:
            return None

        return {
            "id": verse.id,
            "chapter": verse.chapter,
            "verse_number": verse.verse_number,
            "sanskrit": verse.sanskrit,
            "meaning": (
                verse.translations[0].meaning
                if verse.translations else None
            )
        }

    finally:
        db.close()


# ======================================
# MAIN REPLY GENERATOR
# ======================================

def generate_reply(text: str, user_id: int = None, db = None):
    # Setup baseline configuration
    detected_lang = "en"
    english_query = text
    user_preferred_lang = "en"
    user_profile_summary = ""

    # Fetch user preferences & memory summary if DB session is active
    if db is not None and user_id is not None:
        user_record = db.query(User).filter(User.id == user_id).first()
        if user_record:
            user_preferred_lang = user_record.preferred_language or "en"
            user_profile_summary = user_record.memory_summary or ""

    # 1. Automatic Language Detection & Query Translation (Pre-RAG)
    gemini_client = get_gemini_client()
    if gemini_client:
        try:
            analysis_instruction = (
                f"Analyze the user query. Detect if it is English (en), Hindi (hi), Sanskrit (sa), Tamil (ta), Telugu (te), or Odia (or). "
                "Return a JSON object matching the QueryAnalysis schema containing the 2-letter detected language code (lang) "
                "and the English translation of the query (translated_query). "
                f"If you cannot detect it confidently, set lang to '{user_preferred_lang}' and translated_query to the original query."
            )
            from google.genai import types
            analysis_response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"User Query: '{text}'",
                config=types.GenerateContentConfig(
                    system_instruction=analysis_instruction,
                    response_mime_type="application/json",
                    response_schema=QueryAnalysis,
                    temperature=0.0,
                    http_options=types.HttpOptions(timeout=4.0)
                )
            )
            analysis = QueryAnalysis.model_validate_json(analysis_response.text)
            detected_lang = analysis.lang
            english_query = analysis.translated_query
            print(f"[Language Routing] Detected query language: {detected_lang}")
        except Exception as e:
            print("[Language Routing] Query language detection failed:", e)
            detected_lang = user_preferred_lang

    # ----------------------------------
    # 2️⃣ Run Intelligence Pipeline (on English query for high-quality FAISS/Emotion match)
    # ----------------------------------
    result = gita_pipeline(english_query)

    intent = result.get("intent")
    emotion = result.get("emotion")
    intensity = result.get("intensity", 0.5)
    verse = result.get("verse")
    addiction_flag = result.get("theme") == "self_control"

    # ----------------------------------
    # 3️⃣ Greeting Handling (No Verse)
    # ----------------------------------
    if intent == "greeting":
        explanation = build_response(result=result)
        return {
            "chapter": None,
            "verse_number": None,
            "sanskrit": None,
            "meaning": None,
            "explanation": explanation,
            "emotion": "neutral",
            "intensity": 0.3,
            "confidence": 1.0,
            "crisis": False,
            "memory": None
        }

    # ----------------------------------
    # 4️⃣ Crisis Override (Highest Priority)
    # ----------------------------------
    if result.get("crisis"):
        explanation = build_response(result=result)
        return {
            "chapter": None,
            "verse_number": None,
            "sanskrit": None,
            "meaning": None,
            "explanation": explanation,
            "emotion": emotion,
            "intensity": intensity,
            "confidence": result.get("confidence"),
            "crisis": True,
            "memory": None
        }

    # ----------------------------------
    # 5️⃣ Fallback Verse Logic & Database Translation Fallback
    # ----------------------------------
    if not verse:
        verse = get_emotion_fallback_verse(emotion)

    result["verse"] = verse

    # Get local database translation or call Gemini translation fallback
    translated_meaning = ""
    if verse and verse.get("id") and db:
        translated_meaning = get_verse_translation_with_fallback(db, verse["id"], detected_lang)
    elif verse:
        translated_meaning = verse.get("meaning") or ""

    if verse:
        verse["meaning"] = translated_meaning

    # ----------------------------------
    # 6️⃣ Memory & Spiritual Profile Updates
    # ----------------------------------
    if db is not None and user_id is not None:
        user_memory = get_user_memory(db, user_id)
        memory_data = user_memory.update(
            emotion=emotion,
            intensity=intensity,
            addiction_flag=addiction_flag
        )
        
        # Periodic Memory Summarization Trigger (Every 5 User Messages)
        message_count = db.query(Message).filter(Message.user_id == user_id, Message.sender == "user").count()
        # Trigger summary regeneration on current message count milestones
        if message_count > 0 and message_count % 5 == 0:
            print(f"[Memory Engine] Triggering periodic summary regeneration on turn count: {message_count}")
            regenerate_user_memory_summary(db, user_id)
            # Reload fresh profile summary
            user_record = db.query(User).filter(User.id == user_id).first()
            if user_record:
                user_profile_summary = user_record.memory_summary or ""
    else:
        from ai.ai.memory_engine import ConversationMemory
        temp_memory = ConversationMemory()
        memory_data = temp_memory.update(
            emotion=emotion,
            intensity=intensity,
            addiction_flag=addiction_flag
        )

    # ----------------------------------
    # 7️⃣ Build Final Explanation (Gemini with Local Fallback)
    # ----------------------------------
    gemini_success = False

    if gemini_client and verse:
        try:
            trend_str = memory_data.get("trend", "stable")
            relapse_str = ""
            if memory_data.get("addiction_streak", 0) > 1:
                relapse_str = "Seeker is showing a repeating pattern of struggle."
            
            # Label Spiritual metrics as "Growth Journey Progress" (Advisory only warning included)
            journey_level = memory_data.get("spiritual_score", 0)
            memory_str = (
                f"Growth Journey Progress Level: {journey_level}. Emotional Volatility: {memory_data.get('volatility', 0.0)}. "
                "Warning: The Growth Journey level is strictly an advisory progress indicator, not a clinical psychological score."
            )

            system_instruction = (
                "You are Lord Krishna, the divine teacher from the Bhagavad Gita. "
                "Counsel the Seeker in a warm, gentle, and authoritative tone, matching your character in the Gita. "
                "Structure your reply strictly using the grounding verse provided. "
                f"You must translate and write all text fields in the returned JSON object in the detected language: {detected_lang}.\n"
                "CRITICAL GROUNDING RULES:\n"
                "1. Use ONLY the retrieved grounding verse. Do NOT invent other verses.\n"
                "2. Never fabricate chapter or verse numbers.\n"
                "3. Never generate any Sanskrit text (Devanagari or transliteration) that is not provided in the Retrieved Grounding Verse.\n"
                "4. If no grounding verse is provided, explain general spiritual philosophy (Sankhya Yoga, Karma Yoga, Bhakti Yoga) in your own words, without fabricating quotes or verse numbers."
            )
            
            verse_text = f"Chapter {verse.get('chapter')}, Verse {verse.get('verse_number')}: {translated_meaning}"
            
            import time
            from google.genai import types
            
            max_retries = 3
            backoff_factor = 2.0
            response = None
            
            # Sanitize seeker query input (XSS protection)
            seeker_query_clean = html.escape(text)
            
            for attempt in range(max_retries):
                try:
                    response = gemini_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"""
                        Retrieved Grounding Verse: {verse_text}
                        Seeker Profile Context Summary: {user_profile_summary}
                        Advisory Journey Tracking: {memory_str}
                        Current Trend: {trend_str}
                        {relapse_str}
                        
                        Seeker's Query (English Translation): "{seeker_query_clean}"
                        Primary Emotion: {emotion} (Intensity: {intensity})
                        Target Output Language: {detected_lang}
                        """,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=SeekerGuidance,
                            temperature=0.7,
                            http_options=types.HttpOptions(timeout=8.0)
                        ),
                    )
                    break
                except Exception as ex:
                    print(f"[Gemini Layer] Attempt {attempt + 1} failed: {ex}")
                    if attempt < max_retries - 1:
                        sleep_time = backoff_factor ** attempt
                        time.sleep(sleep_time)
                    else:
                        raise ex
            
            if response and response.text:
                # Validate JSON schema
                guidance = SeekerGuidance.model_validate_json(response.text)
                
                # Format to premium HTML incorporating all 8 sections
                gemini_html = format_krishna_response_to_html(guidance, verse, target_lang=detected_lang)
                
                explanation = {
                    "chapter": verse.get("chapter"),
                    "verse_number": verse.get("verse_number"),
                    "sanskrit": verse.get("sanskrit"),
                    "meaning": translated_meaning,
                    "explanation": gemini_html
                }
                gemini_success = True
                print("[Gemini Layer] Dynamic Krishna response generated successfully.")
            
        except Exception as e:
            print("[Gemini Layer] Call failed, applying local template fallback:", e)

    if not gemini_success:
        explanation = build_response(
            result=result,
            trend=memory_data,
            relapse=memory_data
        )

    # ----------------------------------
    # 8️⃣ Learning Feedback Update
    # ----------------------------------
    if verse and verse.get("id"):
        db_feedback = SessionLocal()
        try:
            mapping = db_feedback.query(EmotionVerseMap).filter(
                EmotionVerseMap.verse_id == verse["id"]
            ).first()
            if mapping:
                mapping.usage_count += 1
                mapping.effectiveness_score += (1 - intensity) * 0.1
                db_feedback.commit()
        except SQLAlchemyError:
            db_feedback.rollback()
        finally:
            db_feedback.close()

    # ----------------------------------
    # 9️⃣ Final Structured Output
    # ----------------------------------
    return {
        "chapter": verse.get("chapter") if verse else None,
        "verse_number": verse.get("verse_number") if verse else None,
        "sanskrit": verse.get("sanskrit") if verse else None,
        "meaning": translated_meaning if verse else None,
        "explanation": explanation,
        "emotion": emotion,
        "intensity": intensity,
        "confidence": result.get("confidence"),
        "crisis": False,
        "memory": memory_data
    }