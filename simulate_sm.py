import cv2
from pose_module import PoseDetector
from config import EXERCISE_CONFIG

detector = PoseDetector()
cap = cv2.VideoCapture("annotated_curls_1784313267.mp4")

lL = EXERCISE_CONFIG["curls"]["landmarks_left"]
lR = EXERCISE_CONFIG["curls"]["landmarks_right"]

down_thr = 120  # the relaxed threshold we pushed
up_thr = 140    # the relaxed threshold we pushed

stage = "up"
reps = 0

frame_idx = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
        
    frame_idx += 1
    detector.find_pose(frame, draw=False)
    lm_list = detector.find_position(frame, draw=False)
    
    if len(lm_list) > max(*lL, *lR):
        left_angle = detector.find_angle(frame, lL[0], lL[1], lL[2], draw=False)
        right_angle = detector.find_angle(frame, lR[0], lR[1], lR[2], draw=False)
        avg_angle = (left_angle + right_angle) / 2.0
        
        # State machine
        if avg_angle < down_thr and stage == "up":
            stage = "down"
            print(f"Frame {frame_idx}: went DOWN (angle {avg_angle:.1f} < {down_thr})")
            
        if avg_angle > up_thr and stage == "down":
            stage = "up"
            reps += 1
            print(f"Frame {frame_idx}: went UP (angle {avg_angle:.1f} > {up_thr}) -> REP {reps}")

cap.release()
print(f"\nTotal Reps: {reps}")
