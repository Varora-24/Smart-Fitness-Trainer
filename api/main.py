import os
import tempfile
import cv2
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import protected core modules exactly as required
from core.data import db, nutrition
from core.data.supplement_data import SUPPLEMENT_INFO
from core.utils.config import EXERCISE_CONFIG, YOGA_POSE_CONFIG
from core.tracking.frame_pipeline import FramePipeline
from core.tracking.pose_module import PoseDetector
from core.tracking.yoga_tracker import YogaPoseTracker

app = FastAPI(title="Arogya Vision API Adapter")

# Configure CORS for Next.js development server and production
cors_origins_env = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

DEVELOPMENT_USER_ID = "dev-test-user-123"

# --- Models ---

class NutritionResponse(BaseModel):
    bmr: float
    tdee: float
    macros: dict

class VideoSummary(BaseModel):
    exercise: str
    total_reps: int
    clean_reps: int
    bad_reps: int
    calories: float
    duration_secs: float
    avg_rep_score: float
    avg_symmetry: float
    avg_form: float
    avg_alignment: Optional[float] = None

class RepData(BaseModel):
    rep_number: int
    symmetry: float
    range_of_motion: float
    posture: float
    control: float
    rep_score: float
    rep_label: str

class YogaScore(BaseModel):
    frame: int
    time_s: float
    score: float

class VideoAnalysisResponse(BaseModel):
    is_yoga: bool
    summary: VideoSummary
    reps: Optional[List[RepData]] = None
    yoga_scores: Optional[List[YogaScore]] = None

# --- Endpoints ---

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/history")
def get_history(exercise: Optional[str] = None, limit: int = 50):
    try:
        rows = db.get_history(exercise=exercise, limit=limit, user_id=DEVELOPMENT_USER_ID)
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nutrition", response_model=NutritionResponse)
def get_nutrition(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str,
    goal: str
):
    try:
        bmr = nutrition.calculate_bmr(weight_kg, height_cm, age, gender)
        tdee = nutrition.calculate_tdee(bmr, activity_level)
        macros = nutrition.calculate_macros(tdee, goal, weight_kg)
        return NutritionResponse(bmr=bmr, tdee=tdee, macros=macros)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid nutrition params: {e}")

@app.get("/api/supplements")
def get_supplements():
    return SUPPLEMENT_INFO

@app.post("/api/analyze-video", response_model=VideoAnalysisResponse)
def analyze_video(file: UploadFile = File(...), exercise: str = Form(...)):
    # Verify file extension (basic validation)
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["mp4", "mov", "avi", "mkv"]:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")

    # Determine if it's yoga
    is_yoga = exercise in YOGA_POSE_CONFIG
    is_rep = exercise in EXERCISE_CONFIG

    if not is_yoga and not is_rep:
        raise HTTPException(status_code=400, detail=f"Unknown exercise key: {exercise}")

    tmp_path = ""
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            # Use synchronous read since the endpoint is now running in FastAPI's threadpool
            content = file.file.read()
            
            # Enforce max upload size (~100MB)
            if len(content) > 100 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")
                
            tmp.write(content)
            tmp_path = tmp.name

        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not read video file")

        src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frms = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_s = total_frms / src_fps

        # FramePipeline / Tracker setup exactly as Streamlit does
        pipeline = None
        detector = None
        yoga_tracker = None
        yoga_scores = []
        
        if is_yoga:
            detector = PoseDetector(video_mode=True)
            yoga_tracker = YogaPoseTracker(exercise)
            out_w, out_h = 1280, 720
        else:
            pipeline = FramePipeline(exercise_key=exercise, in_setup=False, video_mode=True)
            pipeline.voice_muted = True
            
        frame_idx = 0
        
        while True:
            ok, frame = cap.read()
            if not ok:
                break
                
            if is_yoga and detector and yoga_tracker:
                timestamp_ms = int(frame_idx * 1000 / max(src_fps, 1.0))
                # Must invoke _letterbox from FramePipeline to match geometry behavior
                frame_lb = FramePipeline._letterbox(frame, out_w, out_h)
                img = detector.find_pose(frame_lb, draw=False, timestamp_ms=timestamp_ms)
                lm_list = detector.find_position(img, draw=False)
                yoga_tracker.update(detector, img, lm_list, draw=False)
                if yoga_tracker.alignment_score > 0:
                    yoga_scores.append({
                        "frame": frame_idx,
                        "time_s": frame_idx / src_fps,
                        "score": yoga_tracker.alignment_score
                    })
            elif pipeline:
                _ = pipeline.process_frame(frame, src_fps=src_fps)
                
            frame_idx += 1
            
        cap.release()
        
        # Results extraction
        if is_yoga:
            avg_alignment = sum(s["score"] for s in yoga_scores) / len(yoga_scores) if yoga_scores else 0.0
            summary = VideoSummary(
                exercise=exercise,
                total_reps=0,
                clean_reps=0,
                bad_reps=0,
                calories=0.0,
                duration_secs=duration_s,
                avg_rep_score=0.0,
                avg_symmetry=0.0,
                avg_form=0.0,
                avg_alignment=round(avg_alignment, 1)
            )
            return VideoAnalysisResponse(
                is_yoga=True,
                summary=summary,
                yoga_scores=[YogaScore(**s) for s in yoga_scores]
            )
        else:
            raw_summary = pipeline.get_summary()
            total_reps = raw_summary.get("total_reps", 0)
            
            # Exact calorie calculation from Streamlit implementation
            kcal_per_rep = float(EXERCISE_CONFIG[exercise].get("kcal_per_rep", 0.25))
            calories = round(total_reps * kcal_per_rep, 2)
            
            summary = VideoSummary(
                exercise=exercise,
                total_reps=total_reps,
                clean_reps=raw_summary.get("clean_reps", 0),
                bad_reps=raw_summary.get("bad_reps", 0),
                calories=calories,
                duration_secs=raw_summary.get("duration_secs", 0.0),
                avg_rep_score=round(raw_summary.get("avg_rep_score", 0.0), 1),
                avg_symmetry=round(raw_summary.get("avg_symmetry", 0.0), 1),
                avg_form=round(raw_summary.get("avg_form", 0.0), 1),
                avg_alignment=None
            )
            
            # Read intentionally exposed internal feature rows to gather per-rep data
            feature_rows = pipeline.session._all_feature_rows
            reps_list = []
            for i, row in enumerate(feature_rows):
                reps_list.append(RepData(
                    rep_number=i + 1,
                    symmetry=round(row.get("symmetry", 0.0), 1),
                    range_of_motion=round(row.get("range_of_motion", 0.0), 1),
                    posture=round(row.get("posture", 0.0), 1),
                    control=round(row.get("control", 0.0), 1),
                    rep_score=round(row.get("rep_score", 0.0), 1),
                    rep_label=row.get("rep_label", "unknown")
                ))
                
            return VideoAnalysisResponse(
                is_yoga=False,
                summary=summary,
                reps=reps_list
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")
    finally:
        # Mandatory safety cleanup
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
