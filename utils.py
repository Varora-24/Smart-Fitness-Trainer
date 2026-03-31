# ================================================================
#  utils.py  –  UI drawing helpers, smoothing, workout summary
# ================================================================
#  v3 Pro additions:
#   - AngleSmoother  : reusable moving-average class
#   - draw_debug_overlay : advanced stats panel (right side)
#   - draw_stage_indicator : up/down stage badge
#   - draw_rep_quality    : per-rep quality score flash
#   - Updated show_summary: accepts WorkoutSession data
# ================================================================

import cv2
import numpy as np
from collections import deque
from config import (
    COLOR_GREEN, COLOR_RED, COLOR_WHITE, COLOR_BLACK,
    COLOR_ORANGE, COLOR_CYAN, COLOR_YELLOW, COLOR_DARK_GRAY,
    COLOR_PURPLE, COLOR_BLUE,
    FRAME_WIDTH, FRAME_HEIGHT,
    ANGLE_SMOOTH_FRAMES,
)


# ================================================================
#  AngleSmoother  – reusable moving-average filter
# ================================================================
class AngleSmoother:
    """
    Keeps a fixed-length deque of angle samples and returns
    the rolling mean.  Instantiate one per tracked joint.

    Usage
    -----
        smoother = AngleSmoother()
        smooth_angle = smoother.update(raw_angle)
    """

    def __init__(self, window: int = ANGLE_SMOOTH_FRAMES):
        self._buf = deque(maxlen=window)

    def update(self, value: float) -> float:
        """Push a new sample and return the smoothed value."""
        self._buf.append(value)
        return float(np.mean(self._buf))

    def reset(self) -> None:
        self._buf.clear()

    @property
    def ready(self) -> bool:
        """True once the buffer has at least one sample."""
        return len(self._buf) > 0


# ================================================================
#  Drawing helpers
# ================================================================

def draw_rect_alpha(img, pt1, pt2, color, alpha: float = 0.5) -> None:
    """Fill a rectangle with *alpha* transparency (in-place)."""
    overlay = img.copy()
    cv2.rectangle(overlay, pt1, pt2, color, cv2.FILLED)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


# ── Progress bar (right edge) ────────────────────────────────────
def draw_progress_bar(img, percentage: float, color) -> None:
    bar_x1, bar_x2 = FRAME_WIDTH - 90, FRAME_WIDTH - 40
    bar_top, bar_bot = 100, 620

    bar_fill = int(np.interp(percentage, (0, 100), (bar_bot, bar_top)))

    cv2.rectangle(img, (bar_x1, bar_top), (bar_x2, bar_bot),
                  (80, 80, 80), cv2.FILLED)
    cv2.rectangle(img, (bar_x1, bar_fill), (bar_x2, bar_bot),
                  color, cv2.FILLED)
    cv2.rectangle(img, (bar_x1, bar_top), (bar_x2, bar_bot),
                  COLOR_WHITE, 2)
    cv2.putText(img, f'{int(percentage)}%',
                (bar_x1 - 10, bar_top - 10),
                cv2.FONT_HERSHEY_PLAIN, 1.6, color, 2)


# ── Rep counter panel (bottom-left) ──────────────────────────────
def draw_rep_panel(img, reps: int, clean_reps: int, bad_reps: int,
                   last_rep_score: float = -1) -> None:
    draw_rect_alpha(img, (0, 530), (280, 720), COLOR_DARK_GRAY, alpha=0.75)

    cv2.putText(img, str(reps),  (15, 690),
                cv2.FONT_HERSHEY_PLAIN, 5, COLOR_WHITE, 5)
    cv2.putText(img, "REPS",     (15, 548),
                cv2.FONT_HERSHEY_PLAIN, 2, COLOR_CYAN, 2)
    cv2.putText(img, f"Clean: {clean_reps}", (15, 578),
                cv2.FONT_HERSHEY_PLAIN, 1.5, COLOR_GREEN, 2)
    cv2.putText(img, f"Bad:   {bad_reps}",   (15, 605),
                cv2.FONT_HERSHEY_PLAIN, 1.5, COLOR_RED, 2)
    if last_rep_score >= 0:
        score_col = COLOR_GREEN if last_rep_score >= 70 else COLOR_ORANGE
        cv2.putText(img, f"Last:  {int(last_rep_score)}",  (15, 632),
                    cv2.FONT_HERSHEY_PLAIN, 1.5, score_col, 2)


# ── Symmetry + form panel (right side, below progress bar) ───────
def draw_symmetry_panel(img, symmetry_score: float,
                        is_asymmetric: bool) -> None:
    x = FRAME_WIDTH - 140
    draw_rect_alpha(img, (x - 10, 628), (FRAME_WIDTH - 10, 720),
                    COLOR_DARK_GRAY, alpha=0.75)

    color = COLOR_RED if is_asymmetric else COLOR_GREEN
    cv2.putText(img, f"SYM:{int(symmetry_score)}%", (x, 658),
                cv2.FONT_HERSHEY_PLAIN, 1.5, color, 2)

    if is_asymmetric:
        draw_rect_alpha(img, (320, 58), (FRAME_WIDTH - 320, 100),
                        (0, 0, 180), alpha=0.80)
        warn = "Uneven Movement!"
        ww = cv2.getTextSize(warn, cv2.FONT_HERSHEY_PLAIN, 1.8, 2)[0][0]
        cv2.putText(img, warn, (FRAME_WIDTH // 2 - ww // 2, 92),
                    cv2.FONT_HERSHEY_PLAIN, 1.8, COLOR_YELLOW, 2)


# ── Form score badge (top-right) ──────────────────────────────────
def draw_form_score(img, form_score: float) -> None:
    draw_rect_alpha(img, (FRAME_WIDTH - 230, 0),
                    (FRAME_WIDTH - 95, 55), COLOR_DARK_GRAY, alpha=0.78)
    color = (COLOR_GREEN if form_score >= 80
             else COLOR_ORANGE if form_score >= 55
             else COLOR_RED)
    cv2.putText(img, f"Form:{int(form_score)}",
                (FRAME_WIDTH - 220, 40),
                cv2.FONT_HERSHEY_PLAIN, 2.0, color, 2)


# ── Stats panel: calories + timer (top-left) ─────────────────────
def draw_stats_panel(img, calories: float, elapsed_secs: float,
                     reps_per_min: float = 0.0) -> None:
    draw_rect_alpha(img, (0, 0), (330, 100), COLOR_DARK_GRAY, alpha=0.75)
    mins = int(elapsed_secs) // 60
    secs = int(elapsed_secs) % 60
    cv2.putText(img, f"Calories: {calories:.2f} kcal", (10, 28),
                cv2.FONT_HERSHEY_PLAIN, 1.5, COLOR_ORANGE, 2)
    cv2.putText(img, f"Time:  {mins:02d}:{secs:02d}", (10, 58),
                cv2.FONT_HERSHEY_PLAIN, 1.5, COLOR_CYAN, 2)
    if reps_per_min > 0:
        cv2.putText(img, f"RPM:   {reps_per_min:.1f}", (10, 88),
                    cv2.FONT_HERSHEY_PLAIN, 1.5, COLOR_YELLOW, 2)


# ── Exercise name badge (top-centre) ─────────────────────────────
def draw_exercise_badge(img, name: str, auto_mode: bool = False) -> None:
    badge_w = 360
    x = FRAME_WIDTH // 2 - badge_w // 2
    draw_rect_alpha(img, (x, 0), (x + badge_w, 55), (20, 20, 80), alpha=0.85)
    label = f"AUTO: {name}" if auto_mode else name
    cv2.putText(img, label, (x + 15, 40),
                cv2.FONT_HERSHEY_PLAIN, 2.2, COLOR_WHITE, 3)


# ── Stage indicator badge ─────────────────────────────────────────
def draw_stage_indicator(img, stage: str) -> None:
    """Show UP / DOWN stage in the top-right corner."""
    color = COLOR_GREEN if stage == "up" else COLOR_BLUE
    badge_text = f"Stage: {stage.upper()}"
    draw_rect_alpha(img, (FRAME_WIDTH - 90, 58),
                    (FRAME_WIDTH, 100), COLOR_DARK_GRAY, alpha=0.7)
    cv2.putText(img, stage.upper(),
                (FRAME_WIDTH - 85, 95),
                cv2.FONT_HERSHEY_PLAIN, 2.0, color, 2)


# ── Advanced debug overlay (right side panel) ─────────────────────
def draw_debug_overlay(img, debug_info: dict) -> None:
    """
    Render a detailed debug panel on the left side below the rep box.

    debug_info keys (all optional):
        left_angle, right_angle, avg_angle,
        posture_angle, velocity, stage
    """
    panel_y = 340
    draw_rect_alpha(img, (0, panel_y), (220, 530),
                    COLOR_DARK_GRAY, alpha=0.72)

    entries = [
        ("DEBUG", COLOR_CYAN),
        (f"L ang: {debug_info.get('left_angle', 0):.0f}°", COLOR_WHITE),
        (f"R ang: {debug_info.get('right_angle', 0):.0f}°", COLOR_WHITE),
        (f"Avg:   {debug_info.get('avg_angle', 0):.0f}°", COLOR_YELLOW),
        (f"Post:  {debug_info.get('posture_angle', 0):.0f}°", COLOR_ORANGE),
        (f"Vel:   {debug_info.get('velocity', 0):.1f}°/f", COLOR_WHITE),
        (f"Stage: {debug_info.get('stage', '-')}", COLOR_GREEN),
    ]

    y = panel_y + 28
    for text, color in entries:
        cv2.putText(img, text, (8, y),
                    cv2.FONT_HERSHEY_PLAIN, 1.4, color, 1)
        y += 28


# ── Feedback text (centred near bottom) ──────────────────────────
def draw_feedback(img, text: str, color=None) -> None:
    if not text:
        return
    col = color or COLOR_ORANGE
    fw = cv2.getTextSize(text, cv2.FONT_HERSHEY_PLAIN, 2.2, 2)[0][0]
    x  = FRAME_WIDTH // 2 - fw // 2
    draw_rect_alpha(img, (x - 10, FRAME_HEIGHT - 72),
                    (x + fw + 10, FRAME_HEIGHT - 10),
                    COLOR_DARK_GRAY, 0.65)
    cv2.putText(img, text, (x, FRAME_HEIGHT - 22),
                cv2.FONT_HERSHEY_PLAIN, 2.2, col, 2)


# ── FPS counter (bottom-right) ────────────────────────────────────
def draw_fps(img, fps: float) -> None:
    cv2.putText(img, f'FPS:{int(fps)}',
                (FRAME_WIDTH - 120, FRAME_HEIGHT - 12),
                cv2.FONT_HERSHEY_PLAIN, 1.6, COLOR_GREEN, 2)


# ── Keyboard hints (very bottom) ─────────────────────────────────
def draw_hints(img, auto_mode: bool = False) -> None:
    hints = ("[S]Squats [P]Push-Ups [C]Curls [L]Lunges "
             "[H]ShoulderPress [A]Auto [D]Debug [Q]Quit")
    cv2.putText(img, hints, (6, FRAME_HEIGHT - 12),
                cv2.FONT_HERSHEY_PLAIN, 1.1, (140, 140, 140), 1)


# ── Rep-quality flash (centre-screen, brief) ─────────────────────
def draw_rep_quality_flash(img, score: float) -> None:
    """Flash the rep quality score in large text for 1 frame."""
    color = (COLOR_GREEN if score >= 80
             else COLOR_ORANGE if score >= 55
             else COLOR_RED)
    text = f"Rep Score: {int(score)}"
    tw = cv2.getTextSize(text, cv2.FONT_HERSHEY_PLAIN, 3.5, 3)[0][0]
    x  = FRAME_WIDTH // 2 - tw // 2
    draw_rect_alpha(img, (x - 20, FRAME_HEIGHT // 2 - 60),
                    (x + tw + 20, FRAME_HEIGHT // 2 + 20),
                    COLOR_DARK_GRAY, 0.75)
    cv2.putText(img, text, (x, FRAME_HEIGHT // 2 + 10),
                cv2.FONT_HERSHEY_PLAIN, 3.5, color, 3)


# ── Workout summary screen (full-frame) ───────────────────────────
def show_summary(
    reps         : int,
    clean_reps   : int,
    bad_reps     : int,
    calories     : float,
    elapsed_secs : float,
    exercise_name: str,
    avg_symmetry : float = 100.0,
    avg_form     : float = 0.0,
    avg_rep_score: float = 0.0,
    reps_per_min : float = 0.0,
) -> None:
    """Render a full-screen summary and block until a key is pressed."""
    summary = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
    for y in range(FRAME_HEIGHT):
        t = y / FRAME_HEIGHT
        cv2.line(summary, (0, y), (FRAME_WIDTH, y),
                 (int(60 * (1 - t)), 5, int(30 * t)), 1)

    mins = int(elapsed_secs) // 60
    secs = int(elapsed_secs) % 60

    form_color  = COLOR_GREEN if avg_form >= 70 else COLOR_ORANGE
    score_color = COLOR_GREEN if avg_rep_score >= 70 else COLOR_ORANGE

    lines = [
        ("AI FITNESS TRAINER  –  WORKOUT SUMMARY", COLOR_CYAN,   70, 2.6, 2),
        (exercise_name,                            COLOR_WHITE,  130, 2.4, 2),
        (f"Total Reps     :  {reps}",              COLOR_WHITE,  210, 2.1, 2),
        (f"Clean Reps     :  {clean_reps}",        COLOR_GREEN,  250, 2.1, 2),
        (f"Bad Reps       :  {bad_reps}",          COLOR_RED,    290, 2.1, 2),
        (f"Avg Rep Score  :  {avg_rep_score:.1f} / 100", score_color, 330, 2.1, 2),
        (f"Calories       :  {calories:.2f} kcal", COLOR_ORANGE, 370, 2.1, 2),
        (f"Duration       :  {mins:02d}:{secs:02d}", COLOR_CYAN, 410, 2.1, 2),
        (f"Reps / Min     :  {reps_per_min:.1f}",  COLOR_YELLOW, 450, 2.1, 2),
        (f"Avg Symmetry   :  {avg_symmetry:.1f}%", COLOR_YELLOW, 490, 2.1, 2),
        (f"Form Score     :  {avg_form:.1f} / 100", form_color,  530, 2.1, 2),
        ("Press any key to exit", (150, 150, 150), 620, 1.6, 1),
    ]

    for text, color, y, scale, thick in lines:
        tw = cv2.getTextSize(text, cv2.FONT_HERSHEY_PLAIN, scale, thick)[0][0]
        x  = FRAME_WIDTH // 2 - tw // 2
        cv2.putText(summary, text, (x, y),
                    cv2.FONT_HERSHEY_PLAIN, scale, color, thick)

    cv2.line(summary, (80, 90), (FRAME_WIDTH - 80, 90), COLOR_CYAN, 2)
    cv2.imshow(WINDOW_TITLE, summary)
    cv2.waitKey(0)


# Import after definition to avoid circular import issues
try:
    from config import WINDOW_TITLE
except ImportError:
    WINDOW_TITLE = "AI Smart Fitness Trainer v3 Pro"
