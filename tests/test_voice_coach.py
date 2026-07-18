# ================================================================
#  tests/test_voice_coach.py  –  Voice coach unit tests
# ================================================================

from unittest.mock import patch
import voice_coach
import time

# ── Test: Voice Coach Queue ───────────
def test_voice_coach_queue():
    # Enable voice
    with patch("voice_coach.VOICE_ENABLED", True):
        coach = voice_coach.VoiceCoach()

        # Clear queue just in case
        while not voice_coach.tts_queue.empty():
            voice_coach.tts_queue.get()

        # Call say multiple times
        coach.say("Hello")
        coach.say("World")  # Should be dropped due to cooldown

        # Wait a tiny bit for queue
        time.sleep(0.1)

        # Check queue
        assert not voice_coach.tts_queue.empty()
        phrase = voice_coach.tts_queue.get()
        assert phrase == "Hello"
        assert voice_coach.tts_queue.empty()
