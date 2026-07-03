# ================================================================
#  voice_coach.py  –  Async contextual voice coaching  v3 Pro
# ================================================================
#  Non-blocking: speech runs on daemon threads.
#  Cooldown timer prevents phrase spam.
#  Contextual: coach_rep() selects the most relevant phrase.
# ================================================================

import threading
import time
from config import VOICE_ENABLED, VOICE_COOLDOWN_SECS

try:
    import pyttsx3
    _ENGINE_AVAILABLE = True
except ImportError:
    _ENGINE_AVAILABLE = False


class VoiceCoach:
    """
    Fire-and-forget async TTS coach.

    Usage
    -----
        coach = VoiceCoach()
        coach.say("Good rep!")           # generic, always available
        coach.coach_rep(...)             # contextual, after each rep
    """

    def __init__(self):
        self._enabled     = VOICE_ENABLED and _ENGINE_AVAILABLE
        self._last_spoken : float = 0.0
        self._lock        = threading.Lock()
        self._busy        : bool  = False
        self._engine      = None

        if VOICE_ENABLED and not _ENGINE_AVAILABLE:
            print("[VoiceCoach] pyttsx3 not installed – voice disabled.")
            print("            Run:  pip install pyttsx3")

        if self._enabled:
            try:
                self._engine = pyttsx3.init()
                self._engine.setProperty("rate", 155)
            except Exception:
                self._enabled = False

    # ── Public API ────────────────────────────────────────────
    def say(self, phrase: str) -> None:
        """
        Speak *phrase* asynchronously.
        Silently drops if busy or within cooldown.
        """
        if not self._enabled:
            return
        now = time.time()
        with self._lock:
            if self._busy:
                return
            if now - self._last_spoken < VOICE_COOLDOWN_SECS:
                return
            self._busy        = True
            self._last_spoken = now
        threading.Thread(
            target=self._speak, args=(phrase,), daemon=True
        ).start()

    def coach_rep(
        self,
        exercise_key  : str,
        rep_score     : float,
        is_asymmetric : bool,
        bad_posture   : bool,
        rom_ok        : bool,
        velocity_high : bool,
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
            self.say(phrase)

    def enabled(self) -> bool:
        return self._enabled

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
            if self._engine is not None:
                self._engine.say(phrase)
                self._engine.runAndWait()
        except Exception:
            pass
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
