import threading
import time
import logging
import queue
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from config import VOICE_ENABLED, VOICE_COOLDOWN_SECS

logger = logging.getLogger("voice_coach")

# Global queue for Web Speech API polling
tts_queue: queue.Queue[str] = queue.Queue()

class TTSRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            phrase = tts_queue.get_nowait()
        except queue.Empty:
            phrase = None
            
        response = {"phrase": phrase}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def log_message(self, format, *args):
        pass # Suppress logging

def _start_tts_server(port=8081):
    try:
        server = HTTPServer(('0.0.0.0', port), TTSRequestHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        logger.info(f"TTS polling server started on port {port}")
        return server
    except OSError as e:
        logger.warning(f"Could not start TTS server on port {port}: {e}")
        return None

_server_started = False

class VoiceCoach:
    """
    Fire-and-forget async TTS coach using Browser Web Speech API via polling.

    Usage
    -----
        coach = VoiceCoach()
        coach.say("Good rep!")           # generic, always available
        coach.coach_rep(...)             # contextual, after each rep
    """

    def __init__(self):
        global _server_started
        self._enabled     = VOICE_ENABLED
        self._last_spoken : float = 0.0
        self._lock        = threading.Lock()
        self._busy        : bool  = False
        self.muted        : bool  = False

        if VOICE_ENABLED and not _server_started:
            import sys
            if "pytest" not in sys.modules and "pytest" not in sys.argv[0]:
                _start_tts_server()
            _server_started = True

    # ── Public API ────────────────────────────────────────────
    def say(self, phrase: str) -> None:
        """
        Queue *phrase* for the browser to speak.
        Silently drops if busy or within cooldown.
        """
        if not self._enabled or self.muted:
            return
        now = time.time()
        with self._lock:
            if self._busy:
                return
            if now - self._last_spoken < VOICE_COOLDOWN_SECS:
                return
            self._busy        = True
            self._last_spoken = now
            
            # Put phrase into the polling queue
            tts_queue.put(phrase)
            
            # Browser takes time to speak, release busy flag after a short delay
            threading.Timer(2.0, self._release_busy).start()

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
    ) -> None:
        """
        Choose and queue the most contextually relevant phrase
        based on the just-completed rep's quality signals.
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
        if bad_posture:
            return _POSTURE_CUES.get(exercise_key, "Keep good form")
        if is_asymmetric:
            return _ASYMMETRY_CUES.get(exercise_key, "Keep both sides even")
        if not rom_ok:
            return _ROM_CUES.get(exercise_key, "Go deeper")
        if velocity_high:
            return "Slow down and control the movement"
        if rep_score >= 85:
            return _PRAISE_HIGH.get(exercise_key, "Excellent rep!")
        if rep_score >= 65:
            return _PRAISE_MID.get(exercise_key, "Good work, keep it up")
        return ""


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
