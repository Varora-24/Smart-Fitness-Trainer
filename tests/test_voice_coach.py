# ================================================================
#  tests/test_voice_coach.py  –  Voice coach unit tests
# ================================================================

from unittest.mock import MagicMock, patch
import voice_coach

# ── Test 1.4: Single pyttsx3 init call & engine reuse ───────────
@patch("voice_coach.pyttsx3")
def test_voice_coach_single_init(mock_pyttsx3):
    # Mock pyttsx3.init() to return a mock engine
    mock_engine = MagicMock()
    mock_pyttsx3.init.return_value = mock_engine
    
    # Enable voice
    with patch("voice_coach.VOICE_ENABLED", True), \
         patch("voice_coach._ENGINE_AVAILABLE", True):
         
        coach = voice_coach.VoiceCoach()
        
        # Call say multiple times
        coach.say("Hello")
        coach.say("World")
        
        # Verify that pyttsx3.init was called exactly once in __init__
        assert mock_pyttsx3.init.call_count == 1
        
        # Verify rate is set
        mock_engine.setProperty.assert_called_with("rate", 155)
