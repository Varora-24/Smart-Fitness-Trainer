import cv2
from frame_pipeline import FramePipeline

pipeline = FramePipeline("curls", in_setup=False)
cap = cv2.VideoCapture("Screen Recording 2026-07-17 225736.mp4")
frame_idx = 0

prev_stage = None
prev_reps = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame_idx += 1
    
    pipeline.process_frame(frame)
    tracker = pipeline.tracker
    
    if tracker.avg_angle > 0.0:
        print(f"Frame {frame_idx}: avg_angle={tracker.avg_angle:.1f}")
        
    if tracker.stage != prev_stage:
        print(f"Frame {frame_idx}: Stage changed from {prev_stage} to {tracker.stage}. Avg angle: {tracker.avg_angle:.1f}")
        prev_stage = tracker.stage
        
    if tracker.reps != prev_reps:
        print(f"Frame {frame_idx}: Reps changed to {tracker.reps}")
        prev_reps = tracker.reps

print(f"Total reps: {pipeline.tracker.reps}")
