import mediapipe as mp
import numpy as np

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

base_options = BaseOptions(
    model_asset_path="models/pose_landmarker_lite.task",
    delegate=BaseOptions.Delegate.GPU
)
options = PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=VisionRunningMode.IMAGE
)

try:
    with PoseLandmarker.create_from_options(options) as landmarker:
        print("GPU Delegate initialized successfully!")
except Exception as e:
    print(f"Failed to initialize GPU Delegate: {e}")
