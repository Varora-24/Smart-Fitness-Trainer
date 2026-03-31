# ================================================================
#  train_model.py  –  Standalone ML training script
# ================================================================
#  Run AFTER collecting rep data with the trainer:
#
#      python train_model.py
#
#  Reads  : rep_dataset.csv   (collected during workouts)
#  Writes : rep_quality_model.pkl
#
#  Model  : GradientBoostingClassifier (good accuracy, fast predict)
#  Output : probability that a rep is "good_rep" (0.0 – 1.0)
#
#  During runtime, main.py loads the .pkl and blends the ML score
#  with the rule-based score:
#      final = 0.6 * rule_score + 0.4 * ml_prob * 100
# ================================================================

import os
import sys

import numpy as np
import pandas as pd
import pickle

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score

from config import DATASET_CSV_PATH, MODEL_PKL_PATH

# Feature columns used for training
FEATURE_COLS = ["symmetry", "range_of_motion", "posture", "control"]
LABEL_COL    = "rep_label"


def load_data(path: str) -> tuple:
    """Load and validate the dataset CSV."""
    if not os.path.isfile(path):
        print(f"[train] Dataset not found: {path}")
        print("        Run the AI Fitness Trainer and collect reps first.")
        sys.exit(1)

    df = pd.read_csv(path)
    print(f"[train] Loaded {len(df)} rows from {path}")
    print(f"        Label distribution:\n{df[LABEL_COL].value_counts()}\n")

    if len(df) < 20:
        print("[train] WARNING: Very few samples. Collect more reps for "
              "reliable training.")

    X = df[FEATURE_COLS].values.astype(float)
    y = df[LABEL_COL].values
    return X, y


def train(X: np.ndarray, y: np.ndarray) -> GradientBoostingClassifier:
    """Train a GradientBoostingClassifier and report metrics."""
    le = LabelEncoder()
    y_enc = le.fit_transform(y)   # "bad_rep" → 0, "good_rep" → 1

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.20, random_state=42, stratify=y_enc
    )

    model = GradientBoostingClassifier(
        n_estimators  = 150,
        learning_rate = 0.1,
        max_depth     = 3,
        random_state  = 42,
    )
    model.fit(X_train, y_train)

    # Cross-validation
    cv_scores = cross_val_score(model, X, y_enc, cv=5, scoring="accuracy")
    print(f"[train] 5-fold CV accuracy: {cv_scores.mean():.3f} "
          f"(+/- {cv_scores.std():.3f})")

    # Test set report
    y_pred = model.predict(X_test)
    print(f"[train] Test accuracy: {accuracy_score(y_test, y_pred):.3f}")
    print(classification_report(y_test, y_pred,
                                target_names=le.classes_))

    # Attach the label encoder so we can decode predictions later
    model._label_encoder = le
    return model


def save_model(model: GradientBoostingClassifier, path: str) -> None:
    with open(path, "wb") as fh:
        pickle.dump(model, fh)
    print(f"[train] Model saved → {path}")


def main() -> None:
    X, y = load_data(DATASET_CSV_PATH)
    model = train(X, y)
    save_model(model, MODEL_PKL_PATH)
    print("\n[train] Done.  Run `python main.py` to use the model.")


if __name__ == "__main__":
    main()
