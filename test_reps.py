import cv2
from pose_module import PoseDetector
from exercises import ExerciseTracker

detector = PoseDetector()
curls = ExerciseTracker("curls")

cap = cv2.VideoCapture("annotated_curls_1784313267.mp4")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
        
    detector.find_pose(frame, draw=False)
    lm_list = detector.find_position(frame, draw=False)
    
    curls.update(detector, frame, lm_list, draw=False)

print(f"Total reps counted by Curls module: {curls.reps}")
cap.release()
