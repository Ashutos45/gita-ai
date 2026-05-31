# ai/ai/test_gemini_integration.py

import os
import unittest
from unittest.mock import patch, MagicMock
import concurrent.futures

from ai.ai.engine import generate_reply, get_gemini_client, SeekerGuidance

class TestGeminiIntegration(unittest.TestCase):

    def setUp(self):
        self.dummy_text = "I am confused about my duties."
        self.dummy_verse = {
            "id": 1,
            "chapter": 2,
            "verse_number": 47,
            "sanskrit": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन",
            "meaning": "You have a right to perform your prescribed duty, but you are not entitled to the fruits of action."
        }

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""})
    def test_missing_api_key(self):
        """1. Verify that missing API key falls back to local builder immediately."""
        client = get_gemini_client()
        self.assertIsNone(client)
        
        reply = generate_reply(self.dummy_text)
        self.assertIsNotNone(reply)
        self.assertIn("explanation", reply)
        self.assertNotIn('class="krishna-response"', str(reply["explanation"]))

    @patch("google.genai.Client")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "invalid-key"})
    def test_invalid_api_key(self, mock_client_class):
        """2. Verify that invalid API key triggers fallback."""
        with patch("ai.ai.engine.get_gemini_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.side_effect = Exception("API key validation failed: invalid API key")
            mock_get_client.return_value = mock_client
            
            reply = generate_reply(self.dummy_text)
            self.assertIsNotNone(reply)
            self.assertIn("explanation", reply)
            self.assertNotIn('class="krishna-response"', str(reply["explanation"]))

    @patch("ai.ai.engine.get_gemini_client")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "dummy-key"})
    def test_gemini_timeout(self, mock_get_client):
        """3. Verify that client timeout is caught and retried/falls back."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Deadline Exceeded (timeout)")
        mock_get_client.return_value = mock_client
        
        # We mock time.sleep to run tests fast
        with patch("time.sleep") as mock_sleep:
            reply = generate_reply(self.dummy_text)
            self.assertIsNotNone(reply)
            # Verify fallback occurred
            self.assertNotIn('class="krishna-response"', str(reply["explanation"]))
            # Verify it attempted retries (1 for analysis + 3 for guidance = 4 calls)
            self.assertEqual(mock_client.models.generate_content.call_count, 4)

    @patch("ai.ai.engine.get_gemini_client")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "dummy-key"})
    def test_network_failure(self, mock_get_client):
        """4. Verify that network connection refusal triggers fallback."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Connection Refused (Network failure)")
        mock_get_client.return_value = mock_client
        
        with patch("time.sleep"):
            reply = generate_reply(self.dummy_text)
            self.assertIsNotNone(reply)
            self.assertNotIn('class="krishna-response"', str(reply["explanation"]))

    def test_empty_verse_retrieval(self):
        """5. Verify that empty verse retrieval handles grounding without crash (falls back)."""
        # When no verse is found in pipeline and fallback verse fails
        with patch("ai.ai.engine.gita_pipeline") as mock_pipe:
            mock_pipe.return_value = {
                "intent": "general_life",
                "emotion": "confusion",
                "cause": "general",
                "theme": "general",
                "intensity": 0.5,
                "confidence": 0.5,
                "crisis": False,
                "verse": None,
                "semantic_score": 0.0,
                "pattern": "general",
                "relationship_type": "none",
                "addiction_type": "none",
                "original_text": self.dummy_text
            }
            with patch("ai.ai.engine.get_emotion_fallback_verse", return_value=None):
                reply = generate_reply(self.dummy_text)
                self.assertIsNotNone(reply)
                self.assertIsNone(reply["chapter"])
                self.assertIsNone(reply["verse_number"])

    @patch("ai.ai.engine.get_gemini_client")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "dummy-key"})
    def test_malformed_json_response(self, mock_get_client):
        """6. Verify that malformed JSON returned by Gemini fails back gracefully."""
        mock_client = MagicMock()
        # Mock response returning bad JSON
        mock_response = MagicMock()
        mock_response.text = "This is not valid json {"
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        reply = generate_reply(self.dummy_text)
        self.assertIsNotNone(reply)
        # Verify fallback was used instead of raising ValidationError
        self.assertNotIn('class="krishna-response"', str(reply["explanation"]))

    @patch("ai.ai.engine.get_gemini_client")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "dummy-key"})
    def test_concurrent_requests(self, mock_get_client):
        """7. Verify concurrency: Multiple threads can call generate_reply without state contamination."""
        mock_client = MagicMock()
        
        # Smart side-effect to return appropriate JSON based on config type
        def mock_generate_content(model, contents, config, **kwargs):
            mock_resp = MagicMock()
            schema_str = str(config.response_schema if config else "")
            if "QueryAnalysis" in schema_str:
                mock_resp.text = '{"lang": "en", "translated_query": "I am confused about my duties."}'
            else:
                mock_resp.text = (
                    '{"emotional_understanding": "I understand your pain.", '
                    '"why_chosen": "It fits.", '
                    '"personalized_guidance": "Do your duty.", '
                    '"practical_steps": ["Step 1", "Step 2"], '
                    '"reflection_exercise": "Breathe."}'
                )
            return mock_resp
            
        mock_client.models.generate_content.side_effect = mock_generate_content
        mock_get_client.return_value = mock_client
        
        def run_chat():
            return generate_reply(self.dummy_text)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_chat) for _ in range(10)]
            results = [f.result() for f in futures]
            
        for res in results:
            self.assertIsNotNone(res)
            # Should get the formatted response if mocked client succeeded
            self.assertIn('class="krishna-response"', str(res["explanation"]))


if __name__ == "__main__":
    unittest.main()
