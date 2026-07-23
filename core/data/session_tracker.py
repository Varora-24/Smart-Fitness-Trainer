# ================================================================
#  session_tracker.py  –  WorkoutSession analytics
# ================================================================
#  Tracks per-session metrics independently of ExerciseTracker
#  so it survives exercise switches within a session.
#
#  Provides:
#    • WorkoutSession : aggregate stats, CSV export
# ================================================================

import csv
import os
import time
from core.utils.config import DATASET_CSV_PATH


class WorkoutSession:
    """
    Accumulates workout statistics across the entire session,
    even when the user switches exercises.

    Usage
    -----
        session = WorkoutSession()
        session.start()
        ...
        session.record_rep(exercise_key, rep_score, calories)
        ...
        summary = session.summary()
        session.export_csv(feature_rows)
    """

    def __init__(self):
        self._start_time : float = 0.0
        self._rep_log    : list  = []   # list of (timestamp, exercise, score)
        self.total_reps  : int   = 0
        self.clean_reps  : int   = 0
        self.bad_reps    : int   = 0
        self.total_calories: float = 0.0
        self._started    : bool  = False
        self._all_feature_rows: list = []
        self.session_id  : int | None = None

    # ── Lifecycle ────────────────────────────────────────────
    def start(self) -> None:
        self._start_time = time.time()
        self._started    = True

    @property
    def elapsed(self) -> float:
        """Seconds since session.start() was called."""
        if not self._started:
            return 0.0
        return time.time() - self._start_time

    # ── Recording ────────────────────────────────────────────
    def record_rep(
        self,
        exercise_key: str,
        rep_score   : float,
        calories    : float,
        is_clean    : bool,
    ) -> None:
        """Call once per completed rep."""
        self._rep_log.append({
            "time"    : self.elapsed,
            "exercise": exercise_key,
            "score"   : rep_score,
        })
        self.total_reps     += 1
        self.total_calories += calories
        if is_clean:
            self.clean_reps += 1
        else:
            self.bad_reps   += 1

    def add_feature_row(self, row: dict) -> None:
        """Accumulate feature row for CSV/DB export later, and save to DB."""
        self._all_feature_rows.append(row)
        if self.session_id:
            import db
            db.save_rep(self.session_id, row)

    # ── Analytics ────────────────────────────────────────────
    @property
    def reps_per_minute(self) -> float:
        """Average reps per minute over the whole session."""
        mins = self.elapsed / 60.0
        if mins < 0.01:
            return 0.0
        return round(self.total_reps / mins, 1)

    @property
    def avg_rep_score(self) -> float:
        if not self._rep_log:
            return 0.0
        return round(sum(r["score"] for r in self._rep_log) / len(self._rep_log), 1)

    def summary(self) -> dict:
        """Return a dict of all session metrics for the UI."""
        return {
            "total_reps"     : self.total_reps,
            "clean_reps"     : self.clean_reps,
            "bad_reps"       : self.bad_reps,
            "calories"       : round(self.total_calories, 2),
            "duration_secs"  : round(self.elapsed, 1),
            "reps_per_min"   : self.reps_per_minute,
            "avg_rep_score"  : self.avg_rep_score,
        }

    # ── CSV export for ML training ────────────────────────────
    def export_csv(self, feature_rows: list | None = None) -> str:
        """
        Append *feature_rows* (list of dicts from ExerciseTracker)
        to the dataset CSV file.  Creates the file with headers if
        it does not yet exist.

        Returns the path to the CSV file.
        """
        rows_to_export = feature_rows if feature_rows is not None else self._all_feature_rows
        if not rows_to_export:
            return DATASET_CSV_PATH

        fieldnames = [
            "exercise", "symmetry", "range_of_motion",
            "posture", "control", "rep_score", "rep_label",
        ]

        file_exists = os.path.isfile(DATASET_CSV_PATH)
        with open(DATASET_CSV_PATH, "a", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for row in rows_to_export:
                # Write only the columns we defined; ignore extras
                filtered = {k: row.get(k, "") for k in fieldnames}
                writer.writerow(filtered)

        print(f"[Session] Exported {len(rows_to_export)} reps → {DATASET_CSV_PATH}")
        return DATASET_CSV_PATH
