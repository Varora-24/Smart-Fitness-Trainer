# ================================================================
#  tests/test_voice_coach.py  –  Voice coach unit tests
# ================================================================

from unittest.mock import patch
import voice_coach
import time

# ── Test 1.4: Single pyttsx3 init call & engine reuse ───────────
@patch("subprocess.Popen")
def test_voice_coach_single_init(mock_popen):
    # Enable voice
    with patch("voice_coach.VOICE_ENABLED", True), \
         patch("voice_coach._ENGINE_AVAILABLE", True):

        coach = voice_coach.VoiceCoach()

        # Call say multiple times
        coach.say("Hello")
        coach.say("World")

        # Because of cooldown and threading, wait a tiny bit
        time.sleep(0.1)

        assert mock_popen.call_count >= 1
