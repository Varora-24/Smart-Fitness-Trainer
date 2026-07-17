import cv2
import numpy as np
from pose_module import PoseDetector
from config import EXERCISE_CONFIG

detector = PoseDetector()
cap = cv2.VideoCapture("annotated_curls_1784313267.mp4")

frame_count = 0
angles = []

lL = EXERCISE_CONFIG["curls"]["landmarks_left"]
lR = EXERCISE_CONFIG["curls"]["landmarks_right"]

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
        
    frame_count += 1
    # We don't need to actually draw, just find angles
    detector.find_pose(frame, draw=False)
    lm_list = detector.find_position(frame, draw=False)
    
    if len(lm_list) > max(*lL, *lR):
        left_angle = detector.find_angle(frame, lL[0], lL[1], lL[2], draw=False)
        right_angle = detector.find_angle(frame, lR[0], lR[1], lR[2], draw=False)
        avg_angle = (left_angle + right_angle) / 2.0
        angles.append(avg_angle)
    else:
        angles.append(180.0)

cap.release()

# Let's find the peaks and valleys
angles = np.array(angles)
print("\nMinima (curled up):")
# Find local minima (where angle is small)
for i in range(1, len(angles)-1):
    if angles[i] < angles[i-1] and angles[i] < angles[i+1] and angles[i] < 120:
        print(f"Frame {i}: Min angle {angles[i]:.1f}")

print("\nMaxima (arms down):")
for i in range(1, len(angles)-1):
    if angles[i] > angles[i-1] and angles[i] > angles[i+1] and angles[i] > 120:
        print(f"Frame {i}: Max angle {angles[i]:.1f}")
