# ================================================================
#  voice_coach.py  –  Async contextual voice coaching  v3 Pro
# ================================================================
#  Non-blocking: speech runs on daemon threads.
#  Cooldown timer prevents phrase spam.
#  Contextual: coach_rep() selects the most relevant phrase.
# ================================================================

import threading
import time
import logging
from core.utils.config import VOICE_ENABLED, VOICE_COOLDOWN_SECS

logger = logging.getLogger("voice_coach")

try:
    import pyttsx3
    _ENGINE_AVAILABLE = True
except Exception as e:
    import logging
    logging.info(f"pyttsx3 engine not available: {e}")
    pyttsx3 = None  # type: ignore[assignment]
    _ENGINE_AVAILABLE = False


class VoiceCoach:
    """
    Fire-and-forget async TTS coach.

    Two independent channels:
      1. pyttsx3 (desktop / local)  – speaks via the OS TTS engine
      2. Browser TTS                – stores a phrase that Streamlit injects
                                      into the page via Web Speech API

    The two channels are fully independent.  Browser TTS works even when
    pyttsx3 is not installed (e.g., Streamlit Community Cloud).

    Usage
    -----
        coach = VoiceCoach()
        coach.say("Good rep!")           # generic, always available
        coach.coach_rep(...)             # contextual, after each rep
    """

    def __init__(self):
        # pyttsx3 path – only usable locally
        self._pyttsx3_enabled = VOICE_ENABLED and _ENGINE_AVAILABLE
        # Browser TTS path – always available; no library needed
        self._browser_enabled = VOICE_ENABLED

        self._last_spoken : float = 0.0
        self._lock        = threading.Lock()
        self._busy        : bool  = False
        self.muted        : bool  = False

        # Latest phrase queued for browser TTS
        self.browser_phrase : str   = ""
        self.browser_ts     : float = 0.0

        if VOICE_ENABLED and not _ENGINE_AVAILABLE:
            logger.debug("[VoiceCoach] pyttsx3 not installed – desktop TTS disabled; browser TTS still active.")

    # ── Public API ────────────────────────────────────────────
    def get_browser_phrase(self):
        """Returns the latest phrase and its timestamp for Streamlit to read."""
        with self._lock:
            return self.browser_phrase, self.browser_ts

    def say(self, phrase: str, is_browser: bool = False) -> None:
        """
        Speak *phrase* asynchronously.

        Browser path: stores phrase for Web Speech API injection — works on
        Streamlit Cloud with no TTS library installed.
        Desktop path: spawns pyttsx3 in a subprocess (local only).

        Both paths respect the cooldown and muted flag.
        """
        if self.muted:
            return

        now = time.time()

        with self._lock:
            if now - self._last_spoken < VOICE_COOLDOWN_SECS:
                return
            self._last_spoken = now

            if is_browser and self._browser_enabled:
                # Store for Streamlit frontend to inject via Web Speech API.
                # This path does NOT need pyttsx3.
                self.browser_phrase = phrase
                self.browser_ts     = now
                return

            # Desktop pyttsx3 path
            if not self._pyttsx3_enabled:
                return
            if self._busy:
                return
            self._busy = True

        threading.Thread(
            target=self._speak, args=(phrase,), daemon=True
        ).start()

    def _release_busy(self):
        with self._lock:
            self._busy = False

    def coach_rep(
        self,
        exercise_key  : str,
        rep_score     : float,
        is_asymmetric : bool,
        bad_posture   : bool,
        rom_ok        : bool,
        velocity_high : bool,
        is_browser    : bool = False,
    ) -> None:
        """
        Choose and speak the most contextually relevant phrase
        based on the just-completed rep's quality signals.

        Priority: posture > symmetry > ROM > velocity > praise
        """
        phrase = self._select_phrase(
            exercise_key, rep_score,
            is_asymmetric, bad_posture,
            rom_ok, velocity_high,
        )
        if phrase:
            self.say(phrase, is_browser=is_browser)

    def enabled(self) -> bool:
        """True if ANY voice channel is active."""
        return self._pyttsx3_enabled or self._browser_enabled

    # ── Phrase selection ──────────────────────────────────────
    def _select_phrase(
        self,
        exercise_key  : str,
        rep_score     : float,
        is_asymmetric : bool,
        bad_posture   : bool,
        rom_ok        : bool,
        velocity_high : bool,
    ) -> str:
        # Highest priority: posture violations
        if bad_posture:
            return _POSTURE_CUES.get(exercise_key, "Keep good form")

        # Asymmetry
        if is_asymmetric:
            return _ASYMMETRY_CUES.get(exercise_key, "Keep both sides even")

        # Range of motion
        if not rom_ok:
            return _ROM_CUES.get(exercise_key, "Go deeper")

        # Jerky movement
        if velocity_high:
            return "Slow down and control the movement"

        # Positive feedback for good reps
        if rep_score >= 85:
            return _PRAISE_HIGH.get(exercise_key, "Excellent rep!")
        if rep_score >= 65:
            return _PRAISE_MID.get(exercise_key, "Good work, keep it up")

        return ""   # mediocre rep – say nothing rather than spam

    # ── TTS engine ────────────────────────────────────────────
    def _speak(self, phrase: str) -> None:
        try:
            import subprocess
            import sys
            script = f'''
import pyttsx3
try:
    engine = pyttsx3.init()
    engine.setProperty("rate", 155)
    engine.say({repr(phrase)})
    engine.runAndWait()
except Exception as e:
    import logging
    logging.warning(f"Ignored exception in voice_coach.py: {{e}}")
'''
            subprocess.Popen([sys.executable, "-c", script], 
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0)
        except Exception as e:
            logger.debug(f"Voice coach speech failed (non-fatal): {e}")
        finally:
            with self._lock:
                self._busy = False


# ── Phrase libraries ──────────────────────────────────────────────
_POSTURE_CUES = {
    "squats"        : "Keep your back straight",
    "pushups"       : "Keep your body in a straight line",
    "curls"         : "Keep your elbows tucked in",
    "lunges"        : "Keep your torso upright",
    "shoulder_press": "Don't arch your lower back",
}

_ASYMMETRY_CUES = {
    "squats"        : "Balance your weight on both legs",
    "pushups"       : "Keep both arms even",
    "curls"         : "Curl both arms equally",
    "lunges"        : "Control both sides of your lunge",
    "shoulder_press": "Press both arms at the same pace",
}

_ROM_CUES = {
    "squats"        : "Squat deeper for a full range of motion",
    "pushups"       : "Go lower to your chest",
    "curls"         : "Curl all the way up",
    "lunges"        : "Lunge deeper, front knee at ninety degrees",
    "shoulder_press": "Press all the way overhead",
}

_PRAISE_HIGH = {
    "squats"        : "Great squat depth! Keep it up",
    "pushups"       : "Perfect push-up. Well done",
    "curls"         : "Excellent curl. Great control",
    "lunges"        : "Beautiful lunge. Stay balanced",
    "shoulder_press": "Full overhead extension. Fantastic",
}

_PRAISE_MID = {
    "squats"        : "Good squat. Go a little deeper",
    "pushups"       : "Good push-up. Keep the rhythm",
    "curls"         : "Nice curl. Stay controlled",
    "lunges"        : "Good lunge. Stay upright",
    "shoulder_press": "Good press. Squeeze at the top",
}
