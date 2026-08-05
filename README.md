# AI Smart Fitness Trainer v4 Pro

[![CI Verification](https://github.com/Varora-24/Smart-Fitness-Trainer/actions/workflows/ci.yml/badge.svg)](https://github.com/Varora-24/Smart-Fitness-Trainer/actions/workflows/ci.yml)
[![Streamlit Cloud](https://img.shields.io/badge/Streamlit_Cloud-Live_App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://smart-fitness-trainer.streamlit.app)

> 🚧 **Active Development** — This project is being actively expanded. Core
> features (live trainer, video analysis, nutrition, accounts) are functional;
> see [Roadmap](#-roadmap) below for what's in progress and what's planned.

## 🚀 Live Production App

Access the complete real-time WebRTC pose tracking application directly in your browser:
**[👉 Launch Smart Fitness Trainer Live (Streamlit Cloud)](https://smart-fitness-trainer.streamlit.app)**
*(No local installation or intermediate pages required)*

---

An advanced AI-powered fitness training application that uses computer vision and machine learning to provide real-time exercise tracking, form analysis, and personalized coaching feedback.

![AI Fitness Trainer](https://img.shields.io/badge/AI--Powered-Fitness-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-red?style=for-the-badge)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-orange?style=for-the-badge)


- **Single-Person Tracking**: The current pipeline is optimized for tracking a single person in the frame.
- **Lighting Conditions**: MediaPipe performance degrades under low-light conditions or heavy motion blur.
- **Docker Device Mapping**: Webcam access inside Docker containers requires mapping `/dev/video0` which is only natively supported on Linux hosts.
- **Safe Model Loading**: We use `skops` instead of Python's standard `pickle` library to safely serialize and deserialize the trained scikit-learn models, avoiding arbitrary code execution vulnerabilities (Bandit B301/B403).

## 🗺️ Roadmap

### ✅ Completed
- [x] **Live WebRTC Trainer** — real-time pose tracking in the browser
- [x] **Workout History Dashboard** — session analytics with charts
- [x] **User Accounts** — Supabase Auth for robust login and signup
- [x] **Video-Upload Posture Analysis** — upload exercise videos for automated form scoring
- [x] **Macro / Nutrition Calculator** — Mifflin-St Jeor BMR, TDEE, and macro targets
- [x] **Supplement Info (Educational)** — goal-based supplement reference, static data only
- [x] **Migrate to MediaPipe Tasks API** — Migrated `pose_module.py` to the Tasks API and unpinned dependencies, resolving PYSEC-2026-1805.
- [x] **Yoga Coach** — hold-based pose tracking with alignment scoring, joint correction cues, and a 6-pose library (Mountain, Tree, Warrior I & II, Chair, Triangle)

### 🔜 Planned
<!-- Keep this list in sync with the Coming Soon section in app/Home.py -->
- [ ] **Google Sign-In** — one-click login via Google OAuth, no password required
- [ ] **Multi-Person Tracking** — independent pose instances per detected person
- [ ] **Mobile-Responsive Layout** — tuned for phones and tablets
- [ ] **Custom Exercise Builder** — record baseline poses to create new exercises
- [ ] **Integration with Wearables** — sync heart rate and metabolic data
- [ ] **AI Workout Planner** — personalised weekly training plans from workout history

## ⚠️ Known Limitations

- **Supplement information is general/educational** — it is not personalised medical or dietary advice. The in-app disclaimer matches this scope.
- **Single-person tracking only** — the pipeline currently tracks one person per frame.
- **Lighting sensitivity** — MediaPipe performance degrades under low-light or heavy motion blur.
- **Docker webcam limitations** — device mapping (`/dev/video0`) is only natively supported on Linux hosts.

---

**Happy Training! 💪**

*Built with using Python, OpenCV, and MediaPipe*
