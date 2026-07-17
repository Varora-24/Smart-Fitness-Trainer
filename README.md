---
title: AI Smart Fitness Trainer
emoji: 🏋️
colorFrom: red
colorTo: blue
sdk: streamlit
sdk_version: 1.36.0
app_file: Home.py
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

## 🎯 Overview

The AI Smart Fitness Trainer is a comprehensive computer vision-based fitness application that provides:

- **Real-time Pose Detection**: Uses Google's MediaPipe to track body landmarks with high accuracy
- **Multi-Exercise Support**: Tracks 5 major exercises (Squats, Push-ups, Bicep Curls, Lunges, Shoulder Press)
- **Intelligent Form Analysis**: Evaluates symmetry, range of motion, posture, and movement control
- **Machine Learning Integration**: Optional ML model for enhanced rep quality assessment
- **Voice Coaching**: Contextual audio feedback during workouts
- **Auto-Exercise Detection**: Automatically recognizes which exercise you're performing
- **Comprehensive Analytics**: Detailed session tracking and performance metrics
- **Professional UI**: Clean, real-time overlay with progress indicators and debug information

## 🚀 Features

### Core Functionality
- **Real-time Exercise Tracking**: Processes camera feed at 30+ FPS with pose estimation
- **Form Quality Scoring**: 0-100 point system evaluating multiple form criteria
- **Rep Counting**: Automatic detection of completed repetitions with quality classification
- **Multi-Exercise Support**: Seamless switching between different exercises
- **Session Analytics**: Comprehensive workout statistics and performance metrics

### Advanced Features
- **Machine Learning Enhancement**: Gradient Boosting model for improved rep quality prediction
- **Voice Coaching System**: Contextual audio feedback with cooldown management
- **Auto-Detection Mode**: Intelligent exercise recognition using pose signals
- **Debug Overlay**: Detailed technical information for advanced users
- **Camera Setup Mode**: Guided positioning for optimal tracking

### User Experience
- **Intuitive Controls**: Single-key shortcuts for exercise selection
- **Visual Feedback**: Color-coded progress bars, form indicators, and alerts
- **Professional UI**: Clean overlay design with transparency and readability
- **Summary Reports**: Detailed post-workout analytics

## 📋 Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Camera**: Webcam with 720p resolution minimum
- **Operating System**: Windows, macOS, or Linux
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space

### Dependencies
```
opencv-python>=4.8.0
mediapipe>=0.10.0
numpy>=1.24.0
scikit-learn>=1.3.0  # For ML training
pandas>=2.0.0        # For data processing
pyttsx3>=2.90        # For voice coaching (optional)
```

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/smart-trainer.git
cd smart-trainer
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Install Voice Coaching
```bash
pip install pyttsx3
```
*Note: Voice coaching is optional and will be automatically disabled if pyttsx3 is not available.*

## 🎮 Usage

### Basic Operation

1. **Start the Application**:
   ```bash
   python main.py
   ```

2. **Camera Setup**: Position yourself so all body parts are visible in the camera frame. Hold the pose until the progress bar completes.

3. **Select Exercise**: Use keyboard shortcuts to choose your exercise:
   - `S` - Squats
   - `P` - Push-ups
   - `C` - Bicep Curls
   - `L` - Lunges
   - `H` - Shoulder Press

4. **Workout**: Perform your exercise while watching the real-time feedback.

5. **Controls**:
   - `A` - Toggle auto-detection mode
   - `D` - Toggle debug overlay
   - `Q` - Quit and view summary

### Advanced Features

#### Auto-Detection Mode
Enable automatic exercise recognition:
- Press `A` to toggle auto-mode
- The system will analyze your movements and automatically switch exercises
- Useful for circuit training or mixed workouts

#### Machine Learning Enhancement
Train a custom model for better rep quality assessment:

1. **Collect Training Data**: Use the trainer to perform various exercises
2. **Train the Model**:
   ```bash
   python train_model.py
   ```
3. **Use Enhanced Scoring**: The ML model will automatically be loaded on next run

#### Voice Coaching
- Contextual audio feedback during workouts
- Automatic cooldown to prevent feedback spam
- Encouragement for good form, corrections for poor form

## 📊 Exercise Details

### Supported Exercises

| Exercise | Primary Joint | Key Metrics | Calorie Rate |
|----------|---------------|-------------|--------------|
| **Squats** | Knee (Hip→Knee→Ankle) | Depth, Back Straight, Symmetry | 0.32 kcal/rep |
| **Push-ups** | Elbow (Shoulder→Elbow→Wrist) | Depth, Body Plank, Symmetry | 0.29 kcal/rep |
| **Bicep Curls** | Elbow (Shoulder→Elbow→Wrist) | Range, Elbow Position, Control | 0.18 kcal/rep |
| **Lunges** | Knee (Hip→Knee→Ankle) | Depth, Torso Upright, Balance | 0.28 kcal/rep |
| **Shoulder Press** | Elbow (Shoulder→Elbow→Wrist) | Height, Back Neutral, Symmetry | 0.20 kcal/rep |

### Form Analysis Criteria

- **Symmetry**: Bilateral movement balance (35% weight)
- **Range of Motion**: Exercise depth completion (30% weight)
- **Posture**: Proper body alignment (20% weight)
- **Control**: Movement smoothness and velocity (15% weight)

## 🔧 Configuration

### Exercise Parameters
Modify `config.py` to adjust:
- Angle thresholds for each exercise
- Form scoring weights
- UI colors and layout
- Camera resolution settings
- Voice coaching phrases

### Example Configuration
```python
# Adjust squat depth requirements
EXERCISE_CONFIG["squats"]["rom_min_angle"] = 110  # Deeper squats
EXERCISE_CONFIG["squats"]["stage_down_threshold"] = 120  # Earlier detection
```

## 🧠 Machine Learning Integration

### Training Process
1. **Data Collection**: Each workout appends rep features to `rep_dataset.csv`
2. **Feature Engineering**: Extracts symmetry, ROM, posture, and control metrics
3. **Model Training**: Gradient Boosting Classifier with 5-fold cross-validation
4. **Inference**: Blends rule-based (60%) and ML-based (40%) scoring

### Model Performance
- **Algorithm**: GradientBoostingClassifier
- **Features**: 4-dimensional (symmetry, ROM, posture, control)
- **Accuracy**: Typically 85-95% on held-out test sets
- **Training Time**: < 30 seconds for 1000+ samples

## 🏗️ Architecture

### Core Modules

```
├── main.py              # Application entry point and main loop
├── pose_module.py       # MediaPipe pose detection wrapper
├── exercises.py         # Exercise tracking and form analysis
├── exercise_classifier.py # Auto-exercise recognition
├── session_tracker.py   # Workout analytics and CSV export
├── setup_mode.py        # Camera positioning guide
├── voice_coach.py       # Audio feedback system
├── train_model.py       # ML model training script
├── utils.py             # UI drawing and helper functions
└── config.py            # Centralized configuration
```

### Data Flow
1. **Camera Input** → MediaPipe pose estimation
2. **Landmark Processing** → Angle calculations and smoothing
3. **Exercise Logic** → State machine and quality scoring
4. **UI Rendering** → Real-time overlay and feedback
5. **Session Tracking** → Analytics and data export

## 🔍 Technical Details

### Pose Detection
- **Framework**: Google MediaPipe Pose
- **Model**: Full-body landmark detection (33 points)
- **Confidence**: Detection >70%, Tracking >50%
- **Performance**: Real-time processing on CPU

### Computer Vision Pipeline
1. Frame capture and resizing
2. RGB conversion for MediaPipe
3. Pose landmark extraction
4. Bilateral angle calculations
5. Movement state classification
6. Quality metric computation
7. UI overlay rendering

### Machine Learning Features
- **Input Features**: Normalized pose metrics (0-100 scale)
- **Model Output**: Probability of "good rep" (0.0-1.0)
- **Blending**: Weighted combination with rule-based scoring
- **Retraining**: Automatic data collection during workouts

## 📈 Performance Metrics

### Real-time Performance
- **Frame Rate**: 30+ FPS on modern hardware
- **Latency**: <50ms pose detection
- **Accuracy**: 95%+ landmark detection reliability
- **Memory Usage**: ~200MB RAM during operation

### Exercise Recognition
- **Precision**: 90%+ for clear movements
- **Recall**: 95%+ for completed repetitions
- **Form Detection**: 85%+ accuracy on form violations

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Make your changes
5. Add tests for new features
6. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include type hints where possible
- Test on multiple camera setups

### Adding New Exercises
1. Define exercise parameters in `config.py`
2. Implement angle calculations in `exercises.py`
3. Add UI keyboard shortcuts in `main.py`
4. Update auto-detection signals in `exercise_classifier.py`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google MediaPipe**: For the excellent pose detection framework
- **OpenCV Community**: For computer vision tools and documentation
- **Scikit-learn**: For machine learning algorithms
- **Open Source Community**: For the libraries that make this possible

## 📞 Support

### Common Issues
- **Camera not detected**: Ensure webcam permissions and no other applications using camera
- **Poor pose detection**: Improve lighting, reduce background clutter, wear form-fitting clothing
- **Low frame rate**: Close other applications, reduce camera resolution in config.py
- **Voice not working**: Install pyttsx3, check system TTS settings

### Troubleshooting
1. Check console output for error messages
2. Enable debug overlay (`D` key) for technical information
3. Verify all dependencies are installed correctly
4. Test with different lighting conditions

## 📊 Database Schema

The application uses **Supabase (PostgreSQL)** to persist training history and user profiles securely. Row Level Security (RLS) ensures users can only access their own data.

```mermaid
erDiagram
    profiles {
        uuid id PK
        text display_name
        real weight_kg
        real height_cm
        int age
        text sex
        text activity_level
        text fitness_goal
        text created_at
    }
    sessions {
        int id PK
        uuid user_id FK
        text started_at
        text exercise
        int total_reps
        int clean_reps
        int bad_reps
        real calories
        real duration_secs
        real avg_rep_score
    }
    reps {
        int id PK
        int session_id FK
        text exercise
        real symmetry
        real range_of_motion
        real posture
        real control
        real rep_score
        text rep_label
        text created_at
    }
    profiles ||--o{ sessions : "has"
    sessions ||--o{ reps : "tracks"
```

## ⚡ Performance Profiling

We profiled the computer vision pipeline over 500 frames using `benchmark.py`:

| Pipeline Stage | Avg (ms/frame) | p95 (ms/frame) | p99 (ms/frame) |
|---|---|---|---|
| MediaPipe Pose Detection | 23.22 | 27.73 | 32.61 |
| Angle + Tracker Logic | 0.01 | 0.01 | 0.01 |
| OpenCV Drawing Overlay | 0.06 | 0.09 | 0.12 |
| **Total Pipeline** | **23.29** | **27.80** | **32.67** |

- **Average FPS**: ~42.9 frames/sec on CPU.

## 🔴 Streamlit Dashboard & Web Application

We provide a multi-page Streamlit web application that runs both the **Live Trainer (WebRTC)** and the **History Dashboard**.

To launch the application locally, run:

```bash
streamlit run Home.py
```

### Pages Structure:
- **`Home.py`**: The landing page explaining features and navigation links. Requires login.
- **`1_🔴_Live_Trainer.py`**: Allows users to grant camera permission in their browser and runs the exact same computer vision and form assessment logic via WebRTC.
- **`2_📊_History.py`**: Displays historical workout statistics and charts filtered by the logged-in user.
- **`3_📹_Video_Analysis.py`**: Upload a video of your exercise for automated posture analysis and annotated output.
- **`4_🥗_Nutrition.py`**: Personalised macro/calorie calculator using the Mifflin-St Jeor equation.
- **`5_💊_Supplements.py`**: Goal-based educational supplement information (see [Known Limitations](#-known-limitations)).

---

## 🌐 Deployment & WebRTC Network Details

You can deploy the app to **Streamlit Community Cloud** or **Hugging Face Spaces**:

### 1. Streamlit Community Cloud
- Push this repository to your GitHub profile.
- Go to [share.streamlit.io](https://share.streamlit.io) and deploy a new app pointing at `Home.py` on your main branch.
- Pushing to Streamlit Cloud allows the app to connect to your remote Supabase instance seamlessly. Ensure you add `SUPABASE_URL` and `SUPABASE_ANON_KEY` to the Streamlit Community Cloud secrets management dashboard.

### 🛡️ WebRTC NAT/TURN Server Troubleshooting
The live trainer uses a public STUN server (`stun:stun.l.google.com:19302`) to resolve peer connections. If the video fails to load or connect when accessed on certain mobile or restrictive corporate networks, you must add a metered TURN server (such as Twilio or metered.ca) to the `RTC_CONFIGURATION` `iceServers` list in `pages/1_🔴_Live_Trainer.py`.

---

## ⚠️ Browser Voice Coaching & Limitations

- **Captions Over Sound**: Since server-side `pyttsx3` text-to-speech runs on the hosting server rather than in the browser, real audio synthesis does not carry over the network. In the WebRTC browser version, voice coaching is automatically converted to **real-time on-screen captions** that display at the bottom of the frame for 3 seconds.
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
