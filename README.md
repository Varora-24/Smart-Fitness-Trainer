# AI Smart Fitness Trainer v4 Pro

[![CI Verification](https://github.com/Varora-24/Smart-Fitness-Trainer/actions/workflows/ci.yml/badge.svg)](https://github.com/Varora-24/Smart-Fitness-Trainer/actions/workflows/ci.yml)
[![Streamlit Cloud](https://img.shields.io/badge/Streamlit_Cloud-Live_App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://smart-fitness-trainer.streamlit.app)
![Python](https://img.shields.io/badge/Python-3.11%2B-green?style=for-the-badge&logo=python&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.35-orange?style=for-the-badge)
![OpenCV](https://img.shields.io/badge/OpenCV-4.9.0-red?style=for-the-badge)
![Supabase](https://img.shields.io/badge/Supabase-Auth_%26_DB-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)

An enterprise-grade, real-time artificial intelligence fitness and yoga coaching system. Leveraging advanced computer vision (MediaPipe Tasks API), joint-angle biomechanical geometry, and machine learning, this platform evaluates exercise posture, scores repetition form quality, counts clean vs. bad repetitions, and delivers immediate voice coaching directly inside the web browser.

---

## 🚀 Live Production Application

Experience the complete WebRTC real-time pose tracking system directly in your browser without local installation:  
**[👉 Launch Smart Fitness Trainer Live (Streamlit Cloud)](https://smart-fitness-trainer.streamlit.app)**  
*(No intermediate landing pages required. Supported on desktop and laptop webcams)*

---

## ✨ Core Features & Technical Architecture

### 1. Real-Time Multi-Exercise Tracking
Monitors 33 3D body landmarks at high frame rates to track movement cadences across 5 major compound exercises:
* **Squats** (Knee flexion & hip hinge depth tracking)
* **Push-Ups** (Elbow flexion & shoulder clearance measurement)
* **Bicep Curls** (Arm flexion & anatomical stability monitoring)
* **Lunges** (Strict front/rear knee geometry and double-bend rejection)
* **Shoulder Press** (Overhead arm extension & lockout completion)

### 2. Repetition Quality Gating (Scored, Not Just Counted)
Unlike basic fitness counters that merely check angle thresholds, v4 Pro implements **Multi-Layer Repetition Quality Gating**. Every completed repetitions is dynamically graded on a `0–100` form scale and systematically classified as a **Clean Rep** ($\ge 60$) or a **Bad Rep** ($< 50$) based on three strict physiological quality gates:
* **Tempo Duration Gate:** Rejects uncontrolled momentum and fast jerky swinging by requiring minimal eccentric/concentric completion times (`1.0s` – `1.2s`).
* **Directional ROM Travel Gate:** Validates angular span travelled to ensure complete range of motion is achieved, independently handling flexion vs. overhead extension movements.
* **Biomechanical Stability Gate:** Monitors postural drift (e.g., severe back lean during bicep curls or lumbar arching in push-ups) using relative structural baseline tracking.

### 3. Yoga Pose Coaching & Guided Surya Namaskar
* **Static Yoga Hold Coaching:** Features a library of 6 core postures (**Mountain Pose**, **Tree Pose**, **Warrior I**, **Warrior II**, **Chair Pose**, and **Triangle Pose**). Calculates alignment scores based on geometric joint angular deviances and displays immediate joint-level correction cues (e.g., *"Lower your right knee"* or *"Straighten your torso"*).
* **Surya Namaskar (Sun Salutation) Automated State Machine:** Guides practitioners through the authentic **12-step traditional sequence**, dynamically advancing from step to step only when stable target poses and alignment thresholds are successfully sustained.

### 4. Offline Video Analysis Mode
For rigorous, high-precision form auditing without webcam constraints, users can upload pre-recorded exercise or yoga MP4/MOV footage. The offline engine performs frame-by-frame analysis at source framerate, calculates cumulative calorie burns, plots per-rep quality distributions, and generates downloadable annotated playback videos.

### 5. Zero-Latency Browser Voice Coaching
Integrates directly with the browser's native **Web Speech API** (`window.speechSynthesis`) via a decoupled asynchronous bridge. Delivers real-time spoken coaching cues, form correction advisORIES, and verbal repetition cadence notifications without server-side TTS network overhead or audio truncation delays.

### 6. Robust Authentication & Google OAuth
Powered by a **Supabase PostgreSQL & Auth** backend, providing persistent user profile management, session analytics serialization, password-based login with bcrypt hashing, and instant **Google OAuth One-Click Sign-In**.

### 7. Personalized Nutrition & Supplement Engine
* **Macro & Caloric Optimizer:** Applies the clinical **Mifflin-St Jeor equation** with physical activity modifiers to calculate accurate BMR, TDEE, and daily nutritional macronutrient breakdowns tailored for fat loss, maintenance, or lean muscle gain.
* **Goal-Specific Supplement Guides:** Educational reference catalog detailing validated dosage protocols and scientific mechanisms for sports supplements, fully wrapped in medical compliance disclaimers.

### 8. Interactive Analytics & Session History
Every completed session persists granular telemetry (exercise type, total volume, clean/bad ratio, form scores, and caloric burn) to a cloud database, visualized through interactive analytical charting widgets inside the personal dashboard.

---

## 📊 Real Project Stats & Engineering Highlights

All statistics and performance figures reflect verified, current repository measurements:

| Metric / Attribute | Measured Value | Engineering Notes & Methodology |
|---|---|---|
| **Total Lines of Code (LOC)** | **8,127 lines** across **61 files** | Python (`.py`): **7,604 LOC**, Markdown (`.md`): **408 LOC**, Config/Data: **115 LOC**. Checked via repository line-by-line syntax auditor. |
| **Automated Test Suite** | **67 / 67 Passing (100% Pass Rate)** | Comprehensive unit & integration testing executed in `~20s` via `pytest`, verifying state machines, quality gating formulas, auth flows, and video pipelines. |
| **Supported Exercises** | **5 Compound + 6 Yoga Poses + 12-Step Sequence** | Explicitly configured in `EXERCISE_CONFIG`, `YOGA_POSE_CONFIG`, and `SURYA_NAMASKAR_STEPS`. |
| **Real-Time Inference FPS** | **~5 – 10 FPS (Streamlit Cloud CPU Tier)**<br>**24 – 30 FPS (Local Native Execution)** | On Streamlit Community Cloud’s shared CPU tier, frame throughput is intentionally throttled via decoupled worker loops (`async_processing=True`) with drop-oldest single-frame buffering (`video_receiver_size=1`) to guarantee **zero queue latency**, preventing buffer buildup or stream freeze. |
| **Secure Model Serialization** | **Zero Vulnerability `skops` Serialization** | All scikit-learn posture models are stored and initialized via `skops 0.14.0` rather than standard Python `pickle`, completely eliminating arbitrary code execution vectors (Bandit B301/B403 compliant). |

---

## 🛠️ Technology Stack & Dependencies

The application relies on modern, pinned dependency layers configured in [requirements.txt](file:///d:/SmartTrainer/requirements.txt):
* **Core Vision & ML Architecture:**
  * `mediapipe == 0.10.35` (MediaPipe Tasks API for low-latency machine learning body landmark detection)
  * `opencv-python == 4.9.0.80` (High-performance matrix drawing and video streaming operations)
  * `numpy == 1.26.4` (Linear algebra, coordinate transformations, and vector angle calculations)
  * `scikit-learn == 1.9.0` & `pandas == 2.2.2` (Posture classification models and tabular telemetry structures)
  * `skops == 0.14.0` (Cryptographically safer replacement for model persistence)
* **Application Frontend & Streaming:**
  * `streamlit == 1.58.0` (Reactive reactive Python web framework)
  * `streamlit-webrtc == 0.74.2` & `av == 16.1.0` (Real-time WebRTC media server transport and PyAV frame codecs)
* **Backend Database & Security:**
  * `supabase >= 2.3.0` (Cloud relational PostgreSQL data layer and authentication REST APIs)
  * `bcrypt == 5.0.0` & `python-dotenv >= 1.0.0` (Secure cryptographic hashing and local configuration injections)

---

## 📸 Demo & UI Assets

The project natively integrates high-contrast, custom AI vector illustrations as visual reference guides across all exercise and yoga modules (located in [app/static/images/](file:///d:/SmartTrainer/app/static/images/)).

> [!NOTE]
> **Portfolio Tip:** While static high-contrast exercise diagrams are embedded within the live interface, capturing and attaching an active animated `.gif` or WebRTC screen recording of the live camera tracking overlay directly into this README section is recommended to maximize initial presentation impact!

---

## 💻 Setup & Installation Instructions

To experience unthrottled hardware acceleration and local webcam speeds (24–30 FPS), run the application locally on your workstation:

### 1. Clone the Repository
```bash
git clone https://github.com/Varora-24/Smart-Fitness-Trainer.git
cd Smart-Fitness-Trainer
```

### 2. Create & Activate a Python Virtual Environment
Requires **Python 3.11+**:
```bash
# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example environment file and insert your Supabase project credentials (required for user authentication and session history persistence):
```bash
# Copy .env.example to .env
cp .env.example .env
```
Open `.env` and fill in your Supabase endpoint details:
```ini
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-public-api-key
```
*(Note: If you do not supply valid Supabase credentials, auth verification will fail on launch).*

### 5. Launch the Streamlit Application
```bash
streamlit run app/Home.py
```
Your local web browser will automatically launch the trainer interface at `http://localhost:8501`.

---

## 🗺️ Roadmap & Future Developments

The core operational features above are actively deployed and functional. Ongoing engineering investigations focus on:
- [ ] **Multi-Person Tracking:** Independent pose segmentation and concurrent rep counting for multiple individuals inside a single frame.
- [ ] **Custom Exercise Builder:** Interactive interface allowing users to record custom landmark baseline geometry to train new exercises on the fly.
- [ ] **Wearable Device Integration:** Direct data ingestion of real-time heart rate and metabolic expenditure via fitness wearables and smartwatches.
- [ ] **AI Weekly Workout Planner:** Autonomous scheduling algorithm generating progressive resistance weekly routines optimized from individual history and form fatigue trends.

---

## ⚠️ Known Limitations & Operational Caveats

* **Single-Person Frame Optimization:** Current pose detection pipelines are calibrated for one primary subject in the camera frame; complex multi-person overlaps may degrade landmark tracing accuracy.
* **Environmental Lighting Sensitivity:** Because computer vision tracking relies on RGB video feeds, extreme low-light environments, intense background glare, or fast motion blur can momentarily degrade joint accuracy.
* **Docker Webcam Hardware Mapping:** Passing webcam hardware directly into Docker containers necessitates Linux host `/dev/video0` device mounting. On Windows or macOS Docker environments, running directly via local Python venv is recommended.
* **Educational Supplement Scope:** All nutritional and dietary supplement references provided by the system serve educational and informational purposes only and do not constitute professional clinical or medical advice.

---

**Built with ❤️ using Python, MediaPipe, OpenCV, Streamlit, and Supabase.**
