# ================================================================
#  benchmark.py  –  Performance profiling and pipeline benchmarks
# ================================================================

import time
import numpy as np
import cv2
from pose_module import PoseDetector
from exercises import ExerciseTracker

def run_benchmark(num_frames: int = 500):
    print(f"Starting performance profiling over {num_frames} frames...")
    
    # ── Initialization ──────────────────────────────────────────
    detector = PoseDetector()
    tracker = ExerciseTracker("squats")
    
    # Generate a synthetic BGR frame (black screen with simple lines to simulate user)
    img = np.zeros((720, 1280, 3), dtype=np.uint8)
    # Draw simple shapes to trigger MediaPipe logic
    cv2.circle(img, (640, 360), 50, (255, 255, 255), -1)
    
    detection_times = []
    logic_times = []
    drawing_times = []
    total_times = []
    
    for i in range(num_frames):
        # We make a copy of the frame to measure drawing time independently without accumulation
        frame = img.copy()
        
        t0 = time.perf_counter()
        
        # 1. Pose detection
        t_det_start = time.perf_counter()
        frame = detector.find_pose(frame, draw=False)
        t_det_end = time.perf_counter()
        detection_times.append((t_det_end - t_det_start) * 1000.0)
        
        # 2. Angle math & tracker logic
        t_logic_start = time.perf_counter()
        lm_list = detector.find_position(frame, draw=False)
        tracker.update(detector, frame, lm_list, draw=False)
        t_logic_end = time.perf_counter()
        logic_times.append((t_logic_end - t_logic_start) * 1000.0)
        
        # 3. Drawing overlay (simulate drawing operations)
        t_draw_start = time.perf_counter()
        # Mocking basic drawing calls to check OpenCV performance
        cv2.putText(frame, "BENCHMARKING", (50, 50), cv2.FONT_HERSHEY_PLAIN, 2.0, (255, 255, 255), 2)
        cv2.rectangle(frame, (10, 10), (100, 100), (0, 255, 0), -1)
        t_draw_end = time.perf_counter()
        drawing_times.append((t_draw_end - t_draw_start) * 1000.0)
        
        t_end = time.perf_counter()
        total_times.append((t_end - t0) * 1000.0)

    # ── Metrics computation ──────────────────────────────────────
    def get_stats(times):
        times = np.array(times)
        return {
            "avg": np.mean(times),
            "p95": np.percentile(times, 95),
            "p99": np.percentile(times, 99)
        }

    det_stats = get_stats(detection_times)
    logic_stats = get_stats(logic_times)
    draw_stats = get_stats(drawing_times)
    tot_stats = get_stats(total_times)
    
    fps = 1000.0 / tot_stats["avg"]
    
    # ── Formatting output ────────────────────────────────────────
    report = f"""
## Performance Profiling Results (500 frames)

| Pipeline Stage | Avg (ms/frame) | p95 (ms/frame) | p99 (ms/frame) |
|---|---|---|---|
| MediaPipe Pose Detection | {det_stats['avg']:.2f} | {det_stats['p95']:.2f} | {det_stats['p99']:.2f} |
| Angle + Tracker Logic | {logic_stats['avg']:.2f} | {logic_stats['p95']:.2f} | {logic_stats['p99']:.2f} |
| OpenCV Drawing Overlay | {draw_stats['avg']:.2f} | {draw_stats['p95']:.2f} | {draw_stats['p99']:.2f} |
| **Total Pipeline** | **{tot_stats['avg']:.2f}** | **{tot_stats['p95']:.2f}** | **{tot_stats['p99']:.2f}** |

**Average FPS**: {fps:.1f} frames/sec
"""
    print(report)
    
    # Save benchmark result to file for reference
    with open("benchmark_results.md", "w") as fh:
        fh.write(report)
    print("Benchmark results saved -> benchmark_results.md")

if __name__ == "__main__":
    run_benchmark()
