# =====================================
# TEST SCRIPT FOR GitaAI ENGINE
# =====================================

from ai.ai.pipeline import gita_pipeline
from ai.ai.response_builder import build_response


def run_test(text: str):

    print("\n==============================")
    print("USER INPUT:")
    print(text)
    print("==============================\n")

    # Step 1: Run intelligence pipeline
    result = gita_pipeline(text)

    # Step 2: Debug Structured Output
    print("---- PIPELINE OUTPUT ----")
    print("Intent:", result["intent"])
    print("Emotion:", result["emotion"])
    print("Cause:", result["cause"])
    print("Theme:", result["theme"])
    print("Intensity:", result["intensity"])
    print("Confidence:", result["confidence"])
    print("Crisis:", result["crisis"])
    print("Semantic Score:", result["semantic_score"])

    if result["verse"]:
        verse = result["verse"]
        print("\nSelected Verse:")
        print("Chapter:", verse.get("chapter"))
        print("Verse:", verse.get("verse_number"))
    else:
        print("\nNo strong semantic match found.")

    # Step 3: Build Final Krishna Response
    final_reply = build_response(result)

    print("\n---- FINAL RESPONSE ----\n")
    print(final_reply)
    print("\n==============================\n")


# =====================================
# RUN DIRECT TEST
# =====================================

if __name__ == "__main__":

    # Change this text to test different emotions
    test_text = "I regret choosing this field."

    run_test(test_text)