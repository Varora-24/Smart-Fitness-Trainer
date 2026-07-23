---
title: AI Smart Fitness Trainer
emoji: 🏋️
colorFrom: red
colorTo: blue
sdk: streamlit
sdk_version: 1.36.0
app_file: app/Home.py
pinned: false
license: mit
---

# AI Smart Fitness Trainer v4 Pro

[![CI Verification](https://github.com/Varora-24/Smart-Fitness-Trainer/actions/workflows/ci.yml/badge.svg)](https://github.com/Varora-24/Smart-Fitness-Trainer/actions/workflows/ci.yml)

> 🚧 **Active Development** — This project is being actively expanded. Core
> features (live trainer, video analysis, nutrition, accounts) are functional;
> see [Roadmap](#-roadmap) below for what's in progress and what's planned.

An advanced AI-powered fitness training application that uses computer vision and machine learning to provide real-time exercise tracking, form analysis, and personalized coaching feedback.

![AI Fitness Trainer](https://img.shields.io/badge/AI--Powered-Fitness-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-red?style=for-the-badge)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-orange?style=for-the-badge)
[![HF Space](https://img.shields.io/badge/🤗_Hugging_Face-Space_Demo-yellow?style=for-the-badge)](https://huggingface.co/spaces/VanshAro/Smart-Fitness-Trainer)


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

### 🔜 Planned
- [ ] **Multi-Person Tracking** — independent pose instances per detected person
- [ ] **Mobile-Responsive Layout** — tuned for phones and tablets
- [ ] **Web Speech API Browser TTS** — client-side speech synthesis
- [ ] **Custom Exercise Builder** — record baseline poses to create new exercises
- [ ] **Integration with Wearables** — sync heart rate and metabolic data

## ⚠️ Known Limitations

- **Supplement information is general/educational** — it is not personalised medical or dietary advice. The in-app disclaimer matches this scope.
- **Single-person tracking only** — the pipeline currently tracks one person per frame.
- **Lighting sensitivity** — MediaPipe performance degrades under low-light or heavy motion blur.
- **Docker webcam limitations** — device mapping (`/dev/video0`) is only natively supported on Linux hosts.

---

**Happy Training! 💪**

*Built with using Python, OpenCV, and MediaPipe*
